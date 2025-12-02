# SystemRDL & SystemVerilog 学习仓库

一个面向芯片设计学习的代码与笔记仓库，包含：
- SystemRDL 寄存器建模示例与练习
- SystemVerilog/Verilog 学习代码与测试平台
- UVM 学习示例（位于 `systemverilog/uvm1/` 等）
- 计划新增：常用、通用、可综合的 RTL 设计模块
- 可能集成：部分开源 IP 模块

## 目录结构

```
systemRDL/        # SystemRDL 学习示例与练习
systemverilog/    # SV/Verilog 学习代码、测试平台与 UVM 示例
  ├─ lab0..lab4   # 分阶段实验与示例（含若干 tb*.sv/.v）
  └─ uvm1/        # UVM 基础用法示例
```

## 快速开始

- 克隆仓库后，浏览对应目录中的 `*.sv`/`*.v`/`*.rdl` 文件与注释。
- 使用你熟悉的 EDA/仿真工具（如 Verilator、VCS、Questa、Icarus Verilog 等）进行本地仿真。
- 典型做法：选择某个 `labX` 下的 `tb*.sv/.v` 作为顶层测试平台进行编译与运行。

示例（以 Icarus Verilog/Verilator 为参考，按需调整）：

```bash
# Verilog 示例（Icarus Verilog）
iverilog -o sim systemverilog/lab1/arbiter.v systemverilog/lab1/tb1.v && vvp sim

# SystemVerilog 示例（Verilator）
verilator -Wall --cc --exe systemverilog/lab2/tb1.sv
```

## 学习建议

- 先从 `systemverilog/lab0` 开始，逐步阅读并运行各 `lab` 的测试平台。
- 对照 `systemRDL` 的示例，理解寄存器建模与硬件寄存器映射的关系。
- UVM 示例从 `systemverilog/uvm1` 开始，聚焦基本类实例化、配置、测试结构。

## 贡献指南

- 欢迎提交 PR：
  - 新增或优化学习示例（SystemRDL/SV/Verilog/UVM）
  - 补充通用、可综合的 RTL 模块
  - 集成合适的开源 IP（注明来源与许可证）
- 请保持目录与文件命名清晰，测试平台可运行，并附简短说明。

## 许可证

- 当前未指定许可证；如需复用或开源集成，请在 PR 中注明拟用许可证并确保兼容性。

## 路线图

- 增补常用可综合 RTL 模块库（FIFO、AXI-lite、定时器等）
- 扩展 UVM 示例，覆盖序列、代理、环境、scoreboard 等
- 引入适配的开源 IP 并增加最小可运行示例

## 参考资料

- Accellera SystemRDL： https://www.accellera.org/downloads/standards/systemrdl
- Accellera UVM： https://www.accellera.org/downloads/standards/uvm
