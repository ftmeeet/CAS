const path = require('path');
const webpack = require('webpack');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = function override(config, env) {
  // Add Cesium to the webpack configuration
  config.resolve.alias = {
    ...config.resolve.alias,
    cesium: path.resolve(__dirname, 'node_modules/cesium/Source')
  };

  // Add plugins to copy Cesium assets
  config.plugins.push(
    new CopyWebpackPlugin({
      patterns: [
        {
          from: 'node_modules/cesium/Build/Cesium',
          to: 'cesium'
        }
      ]
    }),
    new webpack.DefinePlugin({
      CESIUM_BASE_URL: JSON.stringify('/cesium')
    })
  );

  // Add Cesium to the webpack configuration
  config.module.rules.push({
    test: /\.(png|gif|jpg|jpeg|svg|xml|json)$/,
    use: ['url-loader']
  });

  // Add specific rule for Cesium CSS
  config.module.rules.push({
    test: /cesium\/Build\/Cesium\/Widgets\/widgets\.css$/,
    use: [
      'style-loader',
      {
        loader: 'css-loader',
        options: {
          importLoaders: 1
        }
      }
    ]
  });

  // Add general CSS handling
  config.module.rules.push({
    test: /\.css$/,
    exclude: /cesium\/Build\/Cesium\/Widgets\/widgets\.css$/,
    use: [
      'style-loader',
      {
        loader: 'css-loader',
        options: {
          importLoaders: 1
        }
      }
    ]
  });

  return config;
}; 