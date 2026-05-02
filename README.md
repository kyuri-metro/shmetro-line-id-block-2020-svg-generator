# 上海地铁线路号方块 2020 SVG Generator

[![TypeScript](https://img.shields.io/badge/TypeScript-Source%20Package-3178c6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-0f766e.svg)](LICENSE)

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

## 使用例

安装：

```bash
npm install @kyuri-metro/shmetro-line-id-block-2020-svg-generator
```

调用：

```ts
import { generateLineIdBlock2020Svg } from '@kyuri-metro/shmetro-line-id-block-2020-svg-generator'

const svg = generateLineIdBlock2020Svg({
	lineNumber: 21,
	height: 160,
})

document.body.innerHTML = svg
```

自定义颜色：

```ts
import { generateLineIdBlock2020Svg } from '@kyuri-metro/shmetro-line-id-block-2020-svg-generator'

const svg = generateLineIdBlock2020Svg({
	lineNumber: 26,
	height: 120,
	background: '#5F67A9',
	foreground: '#ffffff',
})
```

## 注意

注意：本样式的数字的还原采用了靠左对齐，依赖于字体字形的宽度来取得居中视觉效果，如果在没有 Arial 字体的环境下可能会导致第二个数字过于偏左或偏右。

## 参考资料

- 2020 版参考资料位于 [docs](docs)
- 该目录仅用于仓库留档和人工比对，不参与运行时代码引用
- 该目录已加入 [.npmignore](.npmignore)，不会随 npm 包一起下载