{
  'variables': {
    'vips_version': '<!(node -p "require(\'./lib/libvips\').minimumLibvipsVersion")',
    'platform_and_arch': '<!(node -p "require(\'./lib/platform\')()")',
    'sharp_vendor_dir': './vendor/<(vips_version)/<(platform_and_arch)'
  },
  'targets': [{
    'target_name': 'libvips-cpp-<(vips_version)',
    'conditions': [
      ['OS == "win"', {
        # Build libvips C++ binding for Windows due to MSVC std library ABI changes
        'type': 'shared_library',
        'defines': [
          '_VIPS_PUBLIC=__declspec(dllexport)',
          '_ALLOW_KEYWORD_MACROS',
          'G_DISABLE_ASSERT',
          'G_DISABLE_CAST_CHECKS',
          'G_DISABLE_CHECKS'
        ],
        'sources': [
          'src/libvips/cplusplus/VConnection.cpp',
          'src/libvips/cplusplus/VError.cpp',
          'src/libvips/cplusplus/VImage.cpp',
          'src/libvips/cplusplus/VInterpolate.cpp',
          'src/libvips/cplusplus/VRegion.cpp'
        ],
        'include_dirs': [
          '<(sharp_vendor_dir)/include',
          '<(sharp_vendor_dir)/include/glib-2.0',
          '<(sharp_vendor_dir)/lib/glib-2.0/include'
        ],
        'link_settings': {
          'library_dirs': ['<(sharp_vendor_dir)/lib'],
          'libraries': [
            'libvips.lib',
          ],
        },
        'configurations': {
          'Release': {
            'msvs_settings': {
              "AdditionalOptions": [
                "/std:c++17"
              ],
              'VCCLCompilerTool': {
                'ExceptionHandling': 1,
                'Optimization': 1,
                'WholeProgramOptimization': 'true'
              },
              'VCLibrarianTool': {
                'AdditionalOptions': [
                  '/LTCG:INCREMENTAL'
                ]
              },
              'VCLinkerTool': {
                'ImageHasSafeExceptionHandlers': 'false',
                'OptimizeReferences': 2,
                'EnableCOMDATFolding': 2,
                'LinkIncremental': 1,
                'AdditionalOptions': [
                  '/LTCG:INCREMENTAL'
                ]
              }
            },
            'msvs_disabled_warnings': [
              4275
            ]
          }
        }
      }, {
        # Ignore this target for non-Windows
        'type': 'none'
      }]
    ]
  }, {
    'target_name': 'sharp-<(platform_and_arch)',
    'defines': [
      'G_DISABLE_ASSERT',
      'G_DISABLE_CAST_CHECKS',
      'G_DISABLE_CHECKS',
      'NAPI_VERSION=9',
      'NODE_ADDON_API_DISABLE_DEPRECATED',
      'NODE_API_SWALLOW_UNTHROWABLE_EXCEPTIONS'
    ],
    'dependencies': [
      '<!(node -p "require(\'node-addon-api\').gyp")',
      'libvips-cpp-<(vips_version)'
    ],
    'variables': {
      'conditions': [
        ['OS != "win"', {
          'pkg_config_path': '<!(node -p "require(\'./lib/libvips\').pkgConfigPath()")',
          'use_global_libvips': '<!(node -p "Boolean(require(\'./lib/libvips\').useGlobalLibvips()).toString()")'
        }, {
          'pkg_config_path': '',
          'use_global_libvips': ''
        }]
      ]
    },
    'sources': [
      'src/common.cc',
      'src/metadata.cc',
      'src/stats.cc',
      'src/operations.cc',
      'src/pipeline.cc',
      'src/utilities.cc',
      'src/sharp.cc'
    ],
    'include_dirs': [
      '<!(node -p "require(\'node-addon-api\').include_dir")',
    ],
    'conditions': [
      ['use_global_libvips == "true"', {
        # Use pkg-config for include and lib
        'include_dirs': ['<!@(PKG_CONFIG_PATH="<(pkg_config_path)" pkg-config --cflags-only-I vips-cpp vips glib-2.0 | sed s\/-I//g)'],
        'libraries': ['<!@(PKG_CONFIG_PATH="<(pkg_config_path)" pkg-config --libs vips-cpp)'],
        'conditions': [
          ['OS == "linux"', {
            'defines': [
              # Inspect libvips-cpp.so to determine which C++11 ABI version was used and set _GLIBCXX_USE_CXX11_ABI accordingly. This is quite horrible.
              '_GLIBCXX_USE_CXX11_ABI=<!(if readelf -Ws "$(PKG_CONFIG_PATH="<(pkg_config_path)" pkg-config --variable libdir vips-cpp)/libvips-cpp.so" | c++filt | grep -qF __cxx11;then echo "1";else echo "0";fi)'
            ]
          }]
        ]
      }, {
        # Use pre-built libvips stored locally within node_modules
        'include_dirs': [
          '<(sharp_vendor_dir)/include',
          '<(sharp_vendor_dir)/include/glib-2.0',
          '<(sharp_vendor_dir)/lib/glib-2.0/include'
        ],
        'conditions': [
          ['OS == "win"', {
            'defines': [
              '_ALLOW_KEYWORD_MACROS',
              '_FILE_OFFSET_BITS=64'
            ],
            'link_settings': {
              'library_dirs': ['<(sharp_vendor_dir)/lib'],
              'libraries': [
                'libvips.lib',
              ]
            }
          }],
          ['OS == "mac"', {
            'link_settings': {
              'library_dirs': ['../<(sharp_vendor_dir)/lib'],
              'libraries': [
                'libvips-cpp.<(vips_version).dylib'
              ]
            },
            'xcode_settings': {
              'OTHER_LDFLAGS': [
                # Ensure runtime linking is relative to sharp.node
                '-Wl,-rpath,\'@loader_path/../../<(sharp_vendor_dir)/lib\''
              ]
            }
          }],
          ['OS == "linux"', {
            'defines': [
              '_GLIBCXX_USE_CXX11_ABI=1'
            ],
            'link_settings': {
              'library_dirs': ['../<(sharp_vendor_dir)/lib'],
              'libraries': [
                '-l:libvips-cpp.so.<(vips_version)'
              ],
              'ldflags': [
                # Ensure runtime linking is relative to sharp.node
                '-Wl,-s -Wl,--disable-new-dtags -Wl,-rpath=\'$$ORIGIN/../../<(sharp_vendor_dir)/lib\''
              ]
            }
          }]
        ]
      }]
    ],
    'cflags_cc': [
      '-std=c++17',
      '-fexceptions',
      '-Wall',
      '-Os'
    ],
    'xcode_settings': {
      'CLANG_CXX_LANGUAGE_STANDARD': 'c++17',
      'MACOSX_DEPLOYMENT_TARGET': '10.15',
      'GCC_ENABLE_CPP_EXCEPTIONS': 'YES',
      'GCC_ENABLE_CPP_RTTI': 'YES',
      'OTHER_CPLUSPLUSFLAGS': [
        '-fexceptions',
        '-Wall',
        '-Oz'
      ]
    },
    'configurations': {
      'Release': {
        'conditions': [
          ['OS == "linux"', {
            'cflags_cc': [
              '-Wno-cast-function-type'
            ]
          }],
          ['target_arch == "arm"', {
            'cflags_cc': [
              '-Wno-psabi'
            ]
          }],
          ['OS == "win"', {
            'msvs_settings': {
              'VCCLCompilerTool': {
                "AdditionalOptions": [
                  "/std:c++17"
                ],
                'ExceptionHandling': 1,
                'Optimization': 1,
                'WholeProgramOptimization': 'true'
              },
              'VCLibrarianTool': {
                'AdditionalOptions': [
                  '/LTCG:INCREMENTAL'
                ]
              },
              'VCLinkerTool': {
                'ImageHasSafeExceptionHandlers': 'false',
                'OptimizeReferences': 2,
                'EnableCOMDATFolding': 2,
                'LinkIncremental': 1,
                'AdditionalOptions': [
                  '/LTCG:INCREMENTAL'
                ]
              }
            },
            'msvs_disabled_warnings': [
              4275
            ]
          }]
        ]
      }
    },
  }, {
    'target_name': 'copy-dll',
    'type': 'none',
    'dependencies': [
      'sharp-<(platform_and_arch)'
    ],
    'conditions': [
      ['OS == "win"', {
        'copies': [{
          'destination': 'build/Release',
          'files': [
            '<(sharp_vendor_dir)/lib/libvips-42.dll',
          ]
        }]
      }]
    ]
  }]
}
