# 开发事项

## 当前对应sharp版本

0.34.2

libvip 8.16.1

## 与sharp有何不同？

- sharp0.33.0之后，不再支持本地安装，只能通过npm安装。为了支持 vscode-image-manager 插件本地安装sharp，我fork了sharp，保留了本地安装的逻辑，并同步源码以保持功能与sharp一致

## 不能动的代码

lib/libvips.js
lib/sharp.js

## 需要注意的代码

common.h 不需要判断版本的代码

binding.gyp 谨慎修改

## 开发

- 切到sharp的对应tag，如 0.33.5，然后 git compare 0.34.2
- 查看tag中的更新，并同步到此项目中
- 构建(npm run install)、测试(npm run test)
- bump版本号
- 提交代码到github
