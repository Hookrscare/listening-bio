import js from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "node_modules"] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ["**/*.{ts,tsx}"],
    languageOptions: {
      ecmaVersion: 2020,
      sourceType: "module",
      globals: {
        window: "readonly",
        document: "readonly",
        navigator: "readonly",
        localStorage: "readonly",
        performance: "readonly",
        requestAnimationFrame: "readonly",
        cancelAnimationFrame: "readonly",
        console: "readonly",
        fetch: "readonly",
        Audio: "readonly",
        AudioContext: "readonly",
        AnalyserNode: "readonly",
        HTMLAudioElement: "readonly",
        HTMLCanvasElement: "readonly",
        IntersectionObserver: "readonly",
        Blob: "readonly",
        URL: "readonly",
        FormData: "readonly",
        PointerEvent: "readonly",
        KeyboardEvent: "readonly",
        Uint8Array: "readonly",
        Float32Array: "readonly",
        SVGElement: "readonly",
      },
    },
    rules: {
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "off",
    },
  },
);
