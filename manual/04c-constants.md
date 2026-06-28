# 第4c章 常量与变量完整参考

> **验证状态**: ✅ 已验证  
> **来源**: `pyqalculate_data/variables.json` (1620 行)

---

## 4c.1 数学常量

| 名称 | 别名 | 值 | 来源 |
|------|------|-----|------|
| `pi` | `π` | 3.14159265358979... | variables.json:1398 |
| `e` | — | 2.71828182845905... | variables.json:1400 |
| `euler` | `γ` | ✅ 已识别，可用 `euler + 0` 或 `float(euler)` 获取数值 0.57721566490153... | variables.json:1402 |
| `catalan` | — | ✅ 已识别，可用 `catalan + 0` 或 `float(catalan)` 获取数值 0.91596559417722... | variables.json:1404 |
| `golden` | `φ`, `phi` | ✅ 已识别，可用 `golden + 0` 或 `float(golden)` 获取数值 (1+sqrt(5))/2 | variables.json:1406 |
| `omega` | — | lambertw(1) | variables.json:1408 |
| `pythagoras` | — | sqrt(2) | variables.json:1410 |
| `apery` | — | zeta(3) | variables.json:1412 |
| `tau` | `τ` | 2*pi | variables.json:1414 |
| `plastic` | `ρ`, `rho` | Plastic number | variables.json:1416 |

---

## 4c.2 特殊数字

| 名称 | 值 | 说明 |
|------|-----|------|
| `i` | sqrt(-1) | 虚数单位 |
| `inf` / `infinity` | ∞ | 无穷大 |
| `undefined` | undefined | 未定义 |
| `true` / `yes` | 1 | 真 |
| `false` / `no` | 0 | 假 |

[来源: variables.json:1484-1522]

---

## 4c.3 大数

| 名称 | 值 | 说明 |
|------|-----|------|
| `googolplex` | 10^(10^100) | Googolplex |
| `googol` | 10^100 | Googol |
| `centillion` | 10^303 | Centillion |
| `vigintillion` | 10^63 | Vigintillion |
| `trillion` | 10^12 | 万亿 |
| `billion` | 10^9 | 十亿 |
| `million` | 10^6 | 百万 |
| `thousand` | 10^3 | 千 |
| `hundred` | 10^2 | 百 |
| `lakh` | 10^5 | 印度十万 |
| `crore` | 10^7 | 印度千万 |

[来源: variables.json:49-207]

---

## 4c.4 传统数字

| 名称 | 值 | 说明 |
|------|-----|------|
| `dozen` | 12 | 一打 |
| `bakers_dozen` | 13 | 面包师的一打 |
| `score` | 20 | 二十 |
| `gross` | 144 | 罗（12打） |
| `great_gross` | 1728 | 大罗（12罗） |

[来源: variables.json:210-254]

---

## 4c.5 物理常量 - 通用

| 名称 | 别名 | 值 | 说明 |
|------|------|-----|------|
| `c` | `speed_of_light` | 299792458 m/s | 光速 |
| `planck` | `h` | 6.62607015e-34 J·s | 普朗克常数 |
| `planck2pi` | `ℏ`, `hbar` | 1.054571817e-34 J·s | 约化普朗克常数 |
| `newtonian_constant` | `G` | ⚠️ 返回符号名 `newtonian_constant`，需用 `float(newtonian_constant)` 获取数值 6.6743e-11 m³/(kg·s²) | 万有引力常数 |
| `standard_gravity` | `g_0` | 9.80665 m/s² | 标准重力加速度 |
| `characteristic_impedance` | `Z_0` | 376.730313668 Ω | 特征阻抗 |
| `electric_constant` | `ε_0` | 8.8541878128e-12 F/m | 真空介电常数 |
| `magnetic_constant` | `μ_0` | 1.25663706212e-6 H/m | 真空磁导率 |

[来源: variables.json:258-350]

---

## 4c.6 物理常量 - 电磁学

| 名称 | 别名 | 值 | 说明 |
|------|------|-----|------|
| `elementary_charge` | `q_e`, `e_charge` | 1.602176634e-19 C | 基本电荷 |
| `bohr_magneton` | `μ_B` | 9.2740100783e-24 J/T | 玻尔磁子 |
| `nuclear_magneton` | `μ_N` | 5.0507837461e-27 J/T | 核磁子 |
| `conductance_quantum` | `G_0` | 7.748091729e-5 S | 电导量子 |
| `coulombs_constant` | `k_e` | 8.9875517923e9 N·m²/C² | 库仑常数 |
| `josephson` | `K_J` | 483597.8484...e9 Hz/V | 约瑟夫森常数 |
| `klitzing` | `R_K` | 25812.80745... Ω | 克里青常数 |
| `magnetic_flux_quantum` | `Φ_0` | 2.067833848...e-15 Wb | 磁通量子 |

[来源: variables.json:352-452]

---

## 4c.7 物理常量 - 粒子质量

| 名称 | 值 (u) | 说明 |
|------|--------|------|
| `electron_u` | 0.00054857991 | 电子质量 |
| `proton_u` | 1.007276466621 | 质子质量 |
| `neutron_u` | 1.00866491595 | 中子质量 |
| `deuteron_u` | 2.013553212745 | 氘核质量 |
| `alpha_particle_u` | 4.001506179127 | α粒子质量 |
| `muon_u` | 0.1134289259 | μ子质量 |
| `tau_u` | 1.90754 | τ子质量 |

[来源: variables.json:454-564]

---

## 4c.8 物理常量 - 原子与核

| 名称 | 别名 | 值 | 说明 |
|------|------|-----|------|
| `bohr_radius` | `a_0` | 5.29177210903e-11 m | 玻尔半径 |
| `fine_structure` | `α`, `alpha` | 0.0072973525693 | 精细结构常数 |
| `rydberg` | `R_∞` | 10973731.568160 m⁻¹ | 里德伯常数 |
| `hartree_constant` | `E_h` | 4.3597447222071e-18 J | 哈特里能量 |
| `classical_electron_radius` | `r_e` | 2.8179403262e-15 m | 经典电子半径 |
| `thomson_cross_section` | `σ_t` | 6.6524587321e-29 m² | 汤姆逊截面 |
| `weak_mixing_angle` | `sin2θ_W` | 0.23122 | 弱混合角 |

[来源: variables.json:908-1012]

---

## 4c.9 物理常量 - 物理化学

| 名称 | 别名 | 值 | 说明 |
|------|------|-----|------|
| `avogadro` | `N_A` | 6.02214076e23 mol⁻¹ | 阿伏伽德罗常数 |
| `boltzmann` | `k_B` | 1.380649e-23 J/K | 玻尔兹曼常数 |
| `gas_constant` | `R` | 8.314462618 J/(mol·K) | 气体常数 |
| `faraday` | `ℱ` | 96485.33212 C/mol | 法拉第常数 |
| `stefan` | `σ`, `sigma` | 5.670374419e-8 W/(m²·K⁴) | 斯特藩-玻尔兹曼常数 |
| `wien_displacement` | `b` | 2.897771955e-3 m·K | 维恩位移常数 |
| `first_radiation` | `c_1` | 3.741771852e-16 W·m² | 第一辐射常数 |
| `second_radiation` | `c_2` | 1.4387768775e-2 m·K | 第二辐射常数 |
| `molar_mass` | `M_u` | 0.99999999965e-3 kg/mol | 摩尔质量常数 |
| `atomic_mass_constant` | `m_u` | 1.66053906660e-27 kg | 原子质量常数 |

[来源: variables.json:1016-1227]

---

## 4c.10 能量转换因子

| 名称 | 值 | 说明 |
|------|-----|------|
| `Hz_to_m` | c/Hz | 频率→波长 |
| `Hz_to_J` | h | 频率→能量 |
| `Hz_to_K` | h/k_B | 频率→温度 |
| `Hz_to_kg` | h/c² | 频率→质量 |
| `m_to_Hz` | c/m | 波长→频率 |
| `m_to_J` | h*c/m | 波长→能量 |
| `J_to_Hz` | 1/h | 能量→频率 |
| `J_to_m` | h*c/J | 能量→波长 |
| `J_to_K` | 1/k_B | 能量→温度 |
| `J_to_kg` | 1/c² | 能量→质量 |
| `K_to_Hz` | k_B/h | 温度→频率 |
| `K_to_J` | k_B | 温度→能量 |
| `kg_to_Hz` | c²/h | 质量→频率 |
| `kg_to_J` | c² | 质量→能量 |

[来源: variables.json:1231-1392]

---

## 4c.11 日期时间变量

| 名称 | 说明 |
|------|------|
| `today` | 今天的日期 |
| `tomorrow` | 明天 |
| `yesterday` | 昨天 |
| `now` | 当前日期时间 |

[来源: variables.json:1596-1618]

---

## 4c.12 预定义未知数

| 名称 | 说明 |
|------|------|
| `x`, `y`, `z` | 预定义未知数 |
| `n` | 整数未知数 |
| `ans` | 上次计算结果 |

[来源: variables.json:1564-1593]

---

## 4c.13 矩阵常量

| 名称 | 说明 |
|------|------|
| `pauli_0` | σ₀ (单位矩阵) |
| `pauli_1` | σ₁ (Pauli X) |
| `pauli_2` | σ₂ (Pauli Y) |
| `pauli_3` | σ₃ (Pauli Z) |

[来源: variables.json:1524-1547]
