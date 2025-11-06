// eslint-plugin-greenlint/index.js
"use strict";

function isLoop(node) {
  return ["ForStatement","ForInStatement","ForOfStatement","WhileStatement"].includes(node.type);
}

function walkUp(node, pred) {
  let n = node.parent;
  while (n) { if (pred(n)) return n; n = n.parent; }
  return null;
}

module.exports = {
  rules: {
    // GL-NET-001: fetch/axios in loops → use Promise.all or batching
    "no-network-in-loops": {
      meta: { type: "suggestion", docs: { description: "Avoid network calls inside loops; batch with Promise.all()" } },
      create(context) {
        return {
          CallExpression(node) {
            const callee = node.callee;
            const name = (callee.type === "Identifier" && callee.name)
                       || (callee.type === "MemberExpression" && callee.property && callee.property.name);
            const isNetwork = ["fetch","get","post","put","delete","request","axios","superagent"].includes(String(name));
            if (!isNetwork) return;

            const inLoop = !!walkUp(node, isLoop);
            if (inLoop) {
              context.report({
                node,
                message: "Network call inside loop; prefer batching with Promise.all or concurrency control."
              });
            }
          }
        };
      }
    },

    // GL-WEB-001: Express app without compression middleware
    "express-requires-compression": {
      meta: { type: "suggestion", docs: { description: "Enable gzip/Brotli compression in Express apps." } },
      create(context) {
        let usesExpress = false, usesCompression = false;
        return {
          ImportDeclaration(node) {
            if (node.source.value === "express") usesExpress = true;
            if (node.source.value === "compression") usesCompression = true;
          },
          VariableDeclaration(node) {
            // const compression = require('compression')
            (node.declarations || []).forEach(d => {
              if (d.init && d.init.type === "CallExpression" &&
                  d.init.callee.name === "require" &&
                  d.init.arguments[0] && d.init.arguments[0].value === "compression") {
                usesCompression = true;
              }
            });
          },
          "Program:exit"(node) {
            if (usesExpress && !usesCompression) {
              context.report({
                node,
                message: "Express app detected without compression middleware; enable gzip/Brotli (e.g., compression())."
              });
            }
          }
        };
      }
    },

    // GL-WEB-002: static files should set Cache-Control
    "static-requires-cache-headers": {
      meta: { type: "suggestion", docs: { description: "Set Cache-Control/ETag for static assets." } },
      create(context) {
        let sawExpressStatic = false, sawCacheControl = false;
        return {
          CallExpression(node) {
            const callee = node.callee;
            // app.use(express.static(..., { maxAge: '1d', etag: true }))
            if (callee.type === "MemberExpression" &&
                callee.property && callee.property.name === "use" &&
                node.arguments && node.arguments.length > 0) {
              const arg = node.arguments[0];
              if (arg.type === "CallExpression" &&
                  arg.callee.type === "MemberExpression" &&
                  arg.callee.object && arg.callee.object.name === "express" &&
                  arg.callee.property && arg.callee.property.name === "static") {
                sawExpressStatic = true;
                const opts = node.arguments[1];
                if (opts && opts.type === "ObjectExpression") {
                  const hasMaxAge = opts.properties.some(p => p.key && p.key.name === "maxAge");
                  const hasEtag   = opts.properties.some(p => p.key && p.key.name === "etag");
                  if (hasMaxAge || hasEtag) sawCacheControl = true;
                }
              }
            }
          },
          "Program:exit"(node) {
            if (sawExpressStatic && !sawCacheControl) {
              context.report({
                node,
                message: "Static assets served without explicit cache headers/ETag; set Cache-Control/ETag for efficiency."
              });
            }
          }
        };
      }
    }
  }
};
