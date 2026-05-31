# Industrial Screw Air Compressor Simulation Guide

## Overview

This is a **physics-based simulation** of an industrial screw air compressor, similar to models you'd create in **Simulink** or **AutoCAD/SolidWorks** dynamic simulations. The simulation models real physical interactions between voltage, rotation, pressure, and vibration.

## 🎯 What Makes This Like Simulink?

### 1. **Physics-Based Differential Equations**
Unlike simple parameter mapping, this simulation uses real physics:

- **Motor Dynamics**: Torque = (Voltage × Efficiency) / Speed
- **Rotational Inertia**: τ = I·α (Newton's second law for rotation)
- **Pressure Generation**: Rate proportional to RPM and compression efficiency
- **Load Coupling**: Pressure creates back-pressure that resists rotation
- **Thermal Dynamics**: Heat generation and cooling with time constants

### 2. **Coupled System Behavior**
All parameters interact realistically:

```
Voltage ──→ Motor Torque ──→ Rotation ──→ Compression ──→ Pressure
                ↑                ↓                           ↓
                └────── Load Torque ←──────────────────────┘
                
Rotation + Pressure + Imbalance ──→ Vibration
```

### 3. **Time-Domain Simulation**
- Uses real time steps (dt) for integration
- First-order and second-order dynamics
- Realistic response times and settling behavior

## 🔧 The Four Control Parameters

### 1. **Voltage (0-300V)**
- **What it controls**: Electrical power to the motor
- **Physical effect**: 
  - Higher voltage → More motor torque → Faster rotation
  - But also → More heat generation
- **Realistic range**: 150-220V (normal), >250V (danger)

### 2. **Rotation (0-3000 RPM)**
- **What it controls**: Target motor speed
- **Physical effect**:
  - Higher RPM → More air compression → Higher pressure
  - But also → More vibration from centrifugal forces
  - Limited by motor torque and load
- **Realistic range**: 300-1500 RPM (normal), >2500 RPM (danger)

### 3. **Pressure (0-250 bar)**
- **What it controls**: Target air pressure in tank
- **Physical effect**:
  - Higher pressure → More load on motor → Slower rotation
  - Pressure naturally leaks over time
  - Generation rate depends on RPM
- **Realistic range**: 80-150 bar (normal), >200 bar (danger)

### 4. **Vibration (0-150 mm/s)**
- **What it controls**: Base vibration level (mechanical balance)
- **Physical effect**:
  - Affected by RPM (centrifugal forces)
  - Affected by pressure imbalance
  - Affected by voltage instability
  - Increases with wear over time
- **Realistic range**: 20-60 mm/s (normal), >80 mm/s (danger)

## 🧪 Experiment Scenarios

### Scenario 1: Normal Operation
```
Voltage: 170V
Rotation: 450 RPM
Pressure: 100 bar
Vibration: 40 mm/s
```
**Expected**: Stable operation, all parameters settle to targets

### Scenario 2: High Load Test
```
Voltage: 200V
Rotation: 1500 RPM
Pressure: 180 bar
Vibration: 40 mm/s
```
**Expected**: 
- Motor works harder (high torque)
- Pressure builds up slowly
- Vibration increases due to high RPM
- Temperature rises

### Scenario 3: Overspeed Condition
```
Voltage: 250V
Rotation: 2500 RPM
Pressure: 50 bar
Vibration: 30 mm/s
```
**Expected**:
- Very high rotation achieved
- Excessive vibration (>80 mm/s) - ANOMALY
- Rapid wear accumulation
- Overheating risk

### Scenario 4: Stall Condition
```
Voltage: 120V
Rotation: 200 RPM
Pressure: 200 bar
Vibration: 40 mm/s
```
**Expected**:
- Motor can't overcome load
- Rotation drops below target
- Pressure slowly leaks down
- Possible stall (<100 RPM) - ANOMALY

### Scenario 5: Imbalanced Operation
```
Voltage: 180V
Rotation: 800 RPM
Pressure: 150 bar
Vibration: 80 mm/s
```
**Expected**:
- High base vibration
- Additional vibration from operation
- Total vibration >100 mm/s - ANOMALY
- Accelerated wear

## 📊 Physics Model Details

### Motor Torque Calculation
```python
T_motor = (V × η_motor) / (RPM/1000 + 1) × 10
```
- Higher voltage = more torque
- Higher speed = less torque (back-EMF effect)

### Load Torque (Compression Work)
```python
T_load = (P/100) × (RPM/500) × 5
```
- Proportional to pressure and speed
- Represents work done compressing air

### Rotational Dynamics
```python
α = (T_motor - T_load - T_damping) / I
RPM_new = RPM_old + α × dt × 10
```
- Net torque causes angular acceleration
- Inertia resists changes (realistic lag)

### Pressure Generation
```python
dP/dt = (RPM/500) × η_comp × 2 - leak_rate × P
```
- Generation proportional to RPM
- Natural leakage proportional to pressure

### Vibration Model
```python
V_total = V_base + (RPM/1000)^1.5 × 15 + imbalance_factors
```
- Nonlinear increase with RPM (centrifugal)
- Pressure and voltage imbalance add vibration
- Wear increases vibration over time

## 🎮 How to Use

### 1. Start the Simulator
```bash
cd machine_simulator
python server.py
```
Then open http://localhost:7000

### 2. Adjust Parameters
Use the sliders on the left to change:
- Voltage (V)
- Rotation (RPM)
- Pressure (bar)
- Vibration (mm/s)

### 3. Observe Real-Time Behavior
Watch the telemetry panel (bottom right) for:
- Actual sensor readings (with noise)
- Temperature
- Wear percentage
- Motor and load torque

### 4. Visual Feedback
- **Motor color**: Changes from blue to red as voltage increases
- **Rotation animation**: Speed matches actual RPM
- **Fluid flow**: Speed and opacity reflect pressure
- **Vibration shake**: SVG shakes when vibration is high

## 🔬 Advanced Features

### Temperature Simulation
- Heat generation from electrical losses and friction
- Natural cooling (convection)
- Overheating threshold: 120°C

### Wear Accumulation
- Increases with high RPM and vibration
- Affects vibration levels
- Ranges from 0-100%

### Anomaly Detection
Automatic detection of dangerous conditions:
- Overvoltage (>250V)
- Undervoltage (<100V)
- Stall (<100 RPM)
- Overspeed (>2500 RPM)
- Overpressure (>200 bar)
- Excessive vibration (>80 mm/s)
- Overheating (>120°C)

## 🛠️ Customization

### Modify Physical Constants
Edit `machine_engine.py`:

```python
self.motor_efficiency = 0.85       # Motor efficiency
self.compressor_efficiency = 0.75  # Compression efficiency
self.rotor_inertia = 2.5          # Rotational inertia (kg·m²)
self.bearing_damping = 0.15       # Bearing damping
self.leak_rate = 0.02             # Pressure leak rate
```

### Add New Sensors
Extend the `tick()` method to return additional data:
```python
return {
    # ... existing sensors ...
    "oil_pressure": self.oil_pressure,
    "flow_rate": self.calculate_flow_rate(),
}
```

### Change Operating Limits
```python
self.max_voltage = 300.0
self.max_rotation = 3000.0
self.max_pressure = 250.0
self.max_vibration = 150.0
```

## 📈 Comparison to Simulink

| Feature | This Simulation | Simulink |
|---------|----------------|----------|
| Differential equations | ✅ Yes | ✅ Yes |
| Time-domain integration | ✅ Yes | ✅ Yes |
| Coupled dynamics | ✅ Yes | ✅ Yes |
| Real-time visualization | ✅ Yes | ⚠️ Limited |
| Web-based interface | ✅ Yes | ❌ No |
| Block diagram editor | ❌ No | ✅ Yes |
| Custom blocks | ✅ Python code | ✅ Simulink blocks |

## 🎓 Learning Outcomes

By experimenting with this simulation, you'll understand:

1. **Electromechanical coupling**: How voltage affects mechanical motion
2. **Load dynamics**: How pressure creates back-pressure on the motor
3. **Inertial effects**: Why systems don't respond instantly
4. **Vibration analysis**: Sources of vibration in rotating machinery
5. **Thermal management**: Heat generation and cooling in motors
6. **Wear mechanisms**: How operating conditions affect equipment life

## 🚀 Next Steps

1. **Add PID Controllers**: Implement automatic control loops
2. **Multi-stage Compression**: Model multiple compressor stages
3. **Oil System**: Add oil pressure and temperature
4. **Acoustic Model**: Simulate noise levels
5. **Predictive Maintenance**: Use ML to predict failures
6. **3D Visualization**: Upgrade to Three.js for 3D CAD-like view

---

**Enjoy your physics-based simulation! 🎉**
