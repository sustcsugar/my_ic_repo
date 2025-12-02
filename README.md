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




## 路线图

- [ ] 通用可综合 RTL 模块库：FIFO、AXI-Lite、定时器等
- [ ] UVM 示例扩展：sequence/driver/monitor/env/scoreboard
- [ ] 开源 IP 集成与最小可运行示例
- [ ] SystemRDL → RTL 生成链路示例（PeakRDL 等）
- [ ] 基础仿真脚本 / Makefile（简化编译与运行）
- [ ] 每个 lab 简介与运行指南（简要 README）

## TODO

- [ ] 添加基础 RTL 模块：同步/异步 FIFO、计数器、定时器
- [ ] 提供 AXI-Lite 从设备参考实现与测试平台
- [ ] 增加 SystemRDL 到 RTL 生成演示（以 PeakRDL 为例）
- [ ] 扩充 UVM 示例：factory/config_db、sequence 与 scoreboard 用法
- [ ] 添加简单 CI（格式检查与仿真冒烟）
- [ ] 引入合适的开源 IP 并提供最小可运行 tb
- [ ] 增加 Makefile/脚本统一仿真入口


## 参考资料

- Accellera SystemRDL： https://www.accellera.org/downloads/standards/systemrdl
- PeakRDL： https://peakrdl.readthedocs.io/en/latest/index.html
- Accellera UVM： https://www.accellera.org/downloads/standards/uvm

## 许可证

- 当前未指定许可证；如需复用或开源集成，请在 PR 中注明拟用许可证并确保兼容性。