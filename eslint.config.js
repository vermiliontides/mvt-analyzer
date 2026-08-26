import js from '@eslint/js';
import tseslint from 'typescript-eslint';
 
export default tseslint.config(
  // Global ignores to keep linting out of build artifacts and Python directories
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '**/main-dist/**',
      '**/build/**',
      '**/.venv/**',
      '**/py-packages/**'
    ],
  },
  // Recommended JavaScript baseline rules
  js.configs.recommended,
  // Recommended TypeScript rules across the monorepo
  ...tseslint.configs.recommended,
  {
    files: ['**/*.ts', '**/*.tsx'],
    rules: {
      // Customize any specific monorepo-wide rule preferences here
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  }
);