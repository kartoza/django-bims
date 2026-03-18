/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Webpack configuration for the new React + TypeScript + Chakra UI frontend.
 * This builds the modern frontend at /new/ route.
 */
const webpack = require('webpack');
const path = require('path');
const BundleTracker = require('webpack-bundle-tracker');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const TerserPlugin = require('terser-webpack-plugin');

const isDevelopment = process.env.NODE_ENV !== 'production';

module.exports = {
  mode: isDevelopment ? 'development' : 'production',
  context: __dirname,

  entry: {
    'react-app': ['./static/react/src/index.tsx'],
  },

  output: {
    path: path.join(__dirname, './static/bims/bundles/v2/'),
    filename: isDevelopment ? '[name].js' : '[name]-[contenthash].js',
    chunkFilename: isDevelopment ? '[name].chunk.js' : '[name]-[contenthash].chunk.js',
    publicPath: '/static/bims/bundles/v2/',
  },

  devtool: isDevelopment ? 'source-map' : false,

  plugins: [
    new CleanWebpackPlugin(),
    new BundleTracker({ filename: './webpack-stats-v2.json' }),
    new MiniCssExtractPlugin({
      filename: isDevelopment ? 'css/[name].css' : 'css/[name]-[contenthash].css',
    }),
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development'),
    }),
  ],

  module: {
    rules: [
      // TypeScript and JSX
      {
        test: /\.(ts|tsx)$/,
        exclude: /node_modules/,
        use: [
          {
            loader: 'babel-loader',
            options: {
              presets: [
                '@babel/preset-env',
                '@babel/preset-react',
                '@babel/preset-typescript',
              ],
              plugins: [
                '@babel/plugin-transform-runtime',
              ],
            },
          },
        ],
      },
      // CSS and SCSS
      {
        test: /\.s?css$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          {
            loader: 'sass-loader',
            options: {
              implementation: require('sass'),
            },
          },
        ],
      },
      // Images and fonts
      {
        test: /\.(png|jpg|jpeg|gif|svg|woff|woff2|eot|ttf|otf)$/,
        type: 'asset/resource',
        generator: {
          filename: 'assets/[name]-[hash][ext]',
        },
      },
    ],
  },

  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
    alias: {
      '@': path.resolve(__dirname, 'static/react/src'),
    },
  },

  optimization: {
    minimize: !isDevelopment,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: !isDevelopment,
          },
        },
      }),
    ],
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
        chakra: {
          test: /[\\/]node_modules[\\/]@chakra-ui[\\/]/,
          name: 'chakra',
          chunks: 'all',
          priority: 10,
        },
        maplibre: {
          test: /[\\/]node_modules[\\/]maplibre-gl[\\/]/,
          name: 'maplibre',
          chunks: 'all',
          priority: 10,
        },
      },
    },
  },

  performance: {
    hints: isDevelopment ? false : 'warning',
    maxEntrypointSize: 512000,
    maxAssetSize: 512000,
  },

  watchOptions: {
    ignored: ['node_modules', './**/*.py'],
    aggregateTimeout: 300,
    poll: 1000,
  },

  devServer: {
    static: {
      directory: path.join(__dirname, 'static'),
    },
    hot: true,
    port: 3000,
    proxy: [
      {
        context: ['/api', '/accounts', '/admin'],
        target: 'http://localhost:8000',
      },
    ],
  },
};
