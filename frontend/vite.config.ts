import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import cesium from 'vite-plugin-cesium';
import path from 'path';

export default defineConfig({
  plugins: [react(), cesium()],
  optimizeDeps: {
    exclude: [
      'cesium',
      'resium',
      'satellite.js'
    ],
    include: [
      'mersenne-twister',
      'urijs',
      'grapheme-splitter',
      'bitmap-sdf',
      'lerc',
      'nosleep.js'
    ],
    esbuildOptions: {
      target: 'es2020'
    }
  },
  build: {
    commonjsOptions: {
      include: [/cesium/, /resium/, /satellite.js/, /mersenne-twister/, /urijs/, /grapheme-splitter/, /bitmap-sdf/, /lerc/, /nosleep.js/]
    },
    target: 'es2020'
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      'mersenne-twister': path.resolve(__dirname, 'node_modules/mersenne-twister/src/mersenne-twister.js'),
      'urijs': path.resolve(__dirname, 'node_modules/urijs/src/URI.js'),
      'grapheme-splitter': path.resolve(__dirname, 'node_modules/grapheme-splitter/index.js'),
      'bitmap-sdf': path.resolve(__dirname, 'node_modules/bitmap-sdf/index.js'),
      'lerc': path.resolve(__dirname, 'node_modules/lerc/LercDecode.js'),
      'nosleep.js': path.resolve(__dirname, 'node_modules/nosleep.js/src/index.js')
    },
    extensions: ['.mjs', '.js', '.ts', '.jsx', '.tsx', '.json']
  },
  server: {
    fs: {
      strict: false
    }
  }
}); 