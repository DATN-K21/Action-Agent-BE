module.exports = {
  parser: '@typescript-eslint/parser',
  parserOptions: {
    project: 'tsconfig.json',
    tsconfigRootDir: __dirname,
    sourceType: 'module',
  },
  plugins: ['@typescript-eslint/eslint-plugin'],
  extends: [
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended',
  ],
  root: true,
  env: {
    node: true,
    jest: true,
  },
  ignorePatterns: ['.eslintrc.js'],
  rules: {
    '@typescript-eslint/interface-name-prefix': 'off',
    '@typescript-eslint/explicit-function-return-type': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'off',
    'no-multiple-empty-lines': [
      2,
      {
        'max': 2
      }
    ],
    'semi': [
      2,
      'always'
    ],
    'curly': [
      'warn'
    ],
    'prefer-template': [
      'warn'
    ],
    'space-before-function-paren': [
      0,
      {
        'anonymous': 'never',
        'named': 'never'
      }
    ],
    'camelcase': 0,
    'no-return-assign': 0,
    'quotes': [
      'error',
      'single'
    ],
    '@typescript-eslint/no-non-null-assertion': 'off',
    '@typescript-eslint/no-namespace': 'off',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    'import/no-unresolved': 0,
    'import/order': [
      'warn',
      {
        'groups': [
          'builtin',
          'external',
          'internal',
          'parent',
          'sibling',
          'index',
          'type',
          'object'
        ],
        'newlines-between': 'always'
      }
    ]
  },
  "prettier/prettier": [
    "error",
    {
      "endOfLine": "auto"
    }
  ],
};
