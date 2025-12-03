# IC 设计学习代码库

![SystemRDL](https://img.shields.io/badge/SystemRDL-2.0-blue?style=flat-square)
![SystemVerilog](https://img.shields.io/badge/SystemVerilog-IEEE_1800-green?style=flat-square)
![UVM](https://img.shields.io/badge/UVM-1.2-orange?style=flat-square)
![Verilog](https://img.shields.io/badge/Verilog-IEEE_1364-lightgrey?style=flat-square)

> 渐进式芯片设计学习路径，涵盖寄存器建模、RTL 设计与验证方法学

本仓库提供从入门到进阶的 IC 设计学习资源，包括 **SystemRDL 寄存器建模**、**SystemVerilog/Verilog 设计与验证**、**UVM 验证方法学**三大模块。通过实战案例和渐进式练习，帮助掌握现代芯片设计与验证技术。

## 📂 目录结构

```
systemRDL/
├── labs/
│   ├── lab0/          # 基础寄存器定义与字段属性
│   └── lab1/          # 高级特性：枚举、数组、文档生成
└── projects/
    ├── atcspi/        # ATCSPI200 SPI 控制器寄存器完整定义
    └── uart/          # UART 寄存器地址映射与 UVM 模型

systemverilog/
├── lab0/              # Verilog 基础：MCDT 设计与简单测试
├── lab1/              # SystemVerilog 语法：logic 类型与可配置 task
├── lab2/              # Interface 与 Clocking Block
├── lab3/              # OOP 验证架构：类封装、约束随机、mailbox
├── lab4/              # 完整验证环境：参考模型、寄存器验证、多 package
└── uvm1/              # UVM 入门：组件实例化、配置数据库、测试运行
```

## 🚀 快速开始

### SystemRDL 工具链

使用 [PeakRDL](https://peakrdl.readthedocs.io/) 生成文档、C 头文件、 UVM 寄存器模型和 regblock ：

```bash
# 生成 HTML 文档
peakrdl html systemRDL/labs/lab0/test.rdl -o output/html/

# 生成 C 头文件
peakrdl c-header systemRDL/projects/uart/uart.rdl -o e902_uart.h

# 生成 UVM 寄存器模型
peakrdl uvm systemRDL/projects/atcspi/atcspi.rdl -o uvm_atcspi_pkg.sv

# 生成 regblock
peakrdl regblock systemRDL/projects/atcspi/atcspi.rdl -o regblock/ --cpuif apb3-flat
```

### SystemVerilog 仿真

使用常见 EDA 工具运行测试平台：

```bash
# lab3 - OOP 验证环境（指定测试用例）
vcs -sverilog systemverilog/lab3/tb3.sv +TESTNAME=chnl_burst_test

# lab4 - 完整验证环境
vcs -sverilog systemverilog/lab4/tb.sv -full64 +v2k
```

## 📖 学习路线

| 模块 | 实验 | 技术要点 | 适合人群 |
|------|------|----------|----------|
| **SystemRDL** | lab0 | 基础语法、字段属性、地址映射 | 初学者 |
| | lab1 | 枚举、regfile 数组、Markdown 文档 | 进阶 |
| | projects | 真实 IP 寄存器定义、自动化生成 | 实战 |
| **SystemVerilog** | lab0 | Verilog 基础、MCDT 设计 | 初学者 |
| | lab1 | SV 语法、logic 类型、参数化 task | 入门 SV |
| | lab2 | Interface、Clocking Block、模块化 | 进阶 |
| | lab3 | OOP 架构、约束随机、mailbox 通信 | 验证工程师 |
| | lab4 | 参考模型、寄存器验证、多 package | 高级验证 |
| **UVM** | uvm1 | 组件实例化、config_db、测试运行 | UVM 入门 |

## 🔗 参考资料

- [SystemRDL 2.0 规范](https://www.accellera.org/downloads/standards/systemrdl) - Accellera 官方标准文档
- [PeakRDL 工具套件](https://peakrdl.readthedocs.io/) - 开源 SystemRDL 编译器与生成器
- [UVM 1.2 用户指南](https://www.accellera.org/downloads/standards/uvm) - 通用验证方法学标准
- [SystemVerilog IEEE 1800](https://ieeexplore.ieee.org/document/8299595) - IEEE 官方语言标准