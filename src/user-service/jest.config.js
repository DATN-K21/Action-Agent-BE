/** @type {import('jest').Config} */
const paths = {
    '@/*': ['src/*'],
};

const compilerOptions = { paths };

module.exports = {
    // Recognize these file extensions
    moduleFileExtensions: ['js', 'json', 'ts'],

    // Set the root directory
    rootDir: '.',

    // Regex pattern to find test files (adjust if needed)
    testRegex: '.*\\.spec\\.js$',

    // Specify files for which to collect coverage information
    collectCoverageFrom: ['**/*.(t|j)s'],

    // Directory where Jest should output its coverage files
    coverageDirectory: '../coverage',

    // Use Node environment for testing
    testEnvironment: 'node',

    // Ignore test paths in these directories
    testPathIgnorePatterns: ['/node_modules/', '/dist/'],
};
