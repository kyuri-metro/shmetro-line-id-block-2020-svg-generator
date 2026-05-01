# 上海地铁线路号方块 2020 SVG Generator

> 以下内容为 GPT 5.4 生成，但经过人工正确性检查，你可以作为参考

这是 kyuri-metro 组织下的 2020 版线路号方块 SVG 生成仓库，负责提供单一的纯函数导出接口。

## 示例图

![2020 版线路号方块示例图](https://umamichi.moe/tools/shmetro-idblock/output-example.webp)

统一参数规格：

- foreground
- background
- lineNumber，范围 0 至 99
- height

导出接口位于 [src/index.ts](src/index.ts)。

## 参考资料

- 2020 版参考资料位于 [docs](docs)
- 该目录仅用于仓库留档和人工比对，不参与运行时代码引用
- 该目录已加入 [.npmignore](.npmignore)，不会随 npm 包一起下载