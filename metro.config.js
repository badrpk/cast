const { getDefaultConfig } = require('@react-native/metro-config');

const defaultConfig = getDefaultConfig(__dirname);

module.exports = {
  ...defaultConfig,
  watchFolders: [],
  resolver: {
    sourceExts: ['jsx', 'js', 'ts', 'tsx', 'json'],
    blacklistRE: /node_modules\/.*/ // Exclude node_modules from watching
  },
  transformer: {
    babelTransformerPath: require.resolve('metro-react-native-babel-preset'),
  },
  maxWorkers: 1,
};
