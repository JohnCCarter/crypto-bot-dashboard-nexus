import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";
import pluginReact from "eslint-plugin-react";
import { defineConfig } from "eslint/config";

export default defineConfig([
  {
    files: ["**/*.{js,mjs,cjs,ts,mts,cts,jsx,tsx}"],
    plugins: {
      js,
      "@typescript-eslint": tseslint.plugin,
      react: pluginReact,
    },
    extends: ["js/recommended"],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    settings: {
      react: {
        version: "detect",
      },
    },
    rules: {
      "react/react-in-jsx-scope": "off",
      "@typescript-eslint/no-unused-vars": ["error"],
    },
  },
  tseslint.configs.recommended,
  pluginReact.configs.flat.recommended,
  {
    ignores: [
      "node_modules/**",
      "venv/**",
      "dist/**",
      "build/**",
      "*.min.js",
      "*.bundle.js",
      "coverage/**",
      "*.lcov",
      ".next/**",
      "out/**",
      "**/*.test.js",
      "**/*.test.ts",
      "**/*.test.tsx",
      ".env*",
      "*.log",
      "npm-debug.log*",
      "yarn-debug.log*",
      "yarn-error.log*",
      "pids",
      "*.pid",
      "*.seed",
      "*.pid.lock",
      ".nyc_output",
      ".npm",
      ".eslintcache",
      ".rpt2_cache/",
      ".rts2_cache_cjs/",
      ".rts2_cache_es/",
      ".rts2_cache_umd/",
      ".node_repl_history",
      "*.tgz",
      ".yarn-integrity",
      ".cache",
      ".parcel-cache",
      ".nuxt",
      ".vuepress/dist",
      ".serverless/",
      ".fusebox/",
      ".dynamodb/",
      ".tern-port",
      ".codex_backups/**",
      "temp/**",
    ],
  },
  // Sista blocket: stäng av react/react-in-jsx-scope igen
  {
    rules: {
      "react/react-in-jsx-scope": "off",
    },
  },
]);
