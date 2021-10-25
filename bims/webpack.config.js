const webpack = require('webpack');
let path = require("path");
let BundleTracker = require('webpack-bundle-tracker');
const { CleanWebpackPlugin } = require('clean-webpack-plugin'); // require clean-webpack-plugin
const MiniCssExtractPlugin = require('mini-css-extract-plugin');

module.exports = {
  mode: 'development',
  context: __dirname,

  entry: {
    main: ['./static/react/js/main.jsx'],
    AddSourceReferenceView: ['./static/react/js/AddSourceReferenceView.jsx'],
  },

  output: {
      path: path.join(__dirname, './static/bims/bundles/'),
      filename: "[name]-[hash].js"
  },

  plugins: [
    new CleanWebpackPlugin(),
    new BundleTracker({filename: './webpack-stats.json'}),
    new MiniCssExtractPlugin({filename: 'css/[name]-[hash].css'})
  ],

  module: {
    rules: [
      {
        test: /\.jsx?$/,
        exclude: /(node_modules|bower_components)/,
        use: [
          {
            loader: 'babel-loader',
            options: {
              plugins: [
                 '@babel/syntax-class-properties',
                 '@babel/proposal-class-properties'
              ],
              presets: [
                '@babel/preset-env',
                '@babel/preset-react'
              ]
            }
          }
        ],
      },
      {
        test: /\.s?css$/,
        use: [
          MiniCssExtractPlugin.loader,
          'css-loader',
          {
            loader: 'sass-loader',
            options: {
              implementation: require("sass")
            }
          }
        ]
      },
      {
        test: /\.(png|jpg|jpeg|svg)/,
        use: ['url-loader?limit=100000']
      },
      {
        // shaders
        test: /\.(frag|vert|glsl)$/,
        use: ['raw-loader']
      }
    ]
  },

  resolve: {
    modules: ['node_modules', 'bower_components'],
    extensions: ['.js', '.jsx'],
    fallback: {
      fs: false
    }
  },

  externals: {
    // require("jquery") is external and available
    //  on the global let jQuery
    "jquery": "jQuery",
    "SystemJS": "SystemJS",
    "THREE": "THREE",
    "React": "React",
    "ReactDOM": "ReactDOM"
  },

  watchOptions: {
    ignored: ['node_modules', './**/*.py'],
    aggregateTimeout: 300,
    poll: 1000
  }
}