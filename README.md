# Industrial Screw Air Compressor Simulator

## Overview

This is a physics-based simulation of an industrial screw air compressor, similar to what you'd create in Simulink, AutoCAD, or SolidWorks. It models real physical interactions between four key parameters:

1. Voltage (V) - Electrical power supply
2. Rotation (RPM) - Motor/compressor speed  
3. Pressure (bar) - Compressed air pressure
4. Vibration (mm/s) - Mechanical vibration

## Key Features

### Physics-Based Simulation
- Differential equations for motor dynamics
- Rotational inertia and damping
- Pressure generation and leakage
- Thermal modeling (temperature)
- Wear accumulation over time
- Coupled parameter interactions

### Real-Time Visualization
- Interactive CAD-style 3D visualization
- Live telemetry display
- Animated rotating components
- Fluid flow animation
- Visual feedback (heat, vibration)

### Simulink-Like Behavior
- Time-domain integration
- Coupled system dynamics
- Realistic response curves
- Adjustable parameters in real-time

## Quick Start

### 1. Install Dependencies
```bash
cd machine_simulator
pip install -r requirements.txt
```

### 2. Run the Simulator
```bash
python server.py
```

### 3. Open in Browser
Navigate to: http://localhost:9000

### 4. Adjust Parameters
Use the sliders on the left sidebar to control:
- Voltage: 0-300V (normal: 150-220V)
- Rotation: 0-3000 RPM (normal: 300-1500 RPM)
- Pressure: 0-250 bar (normal: 80-150 bar)
- Vibration: 0-150 mm/s (normal: 20-60 mm/s)

## How It Works

### Physical Model

```
┌─────────────┐
│   Voltage   │──────┐
└─────────────┘      │
                     ▼
              ┌──────────────┐
              │ Motor Torque │
              └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐      ┌──────────────┐
              │   Rotation   │─────▶│  Compression │
              └──────┬───────┘      └──────┬───────┘
                     │                     │
                     │                     ▼
                     │              ┌──────────────┐
                     │              │   Pressure   │
                     │              └──────┬───────┘
                     │                     │
                     │                     │
                     │◀────────────────────┘
                     │    (Load Torque)
                     │
                     ▼
              ┌──────────────┐
              │  Vibration   │
              └──────────────┘
```

### Key Equations

**Motor Torque:**
```
T_motor = (V x efficiency_motor) / (RPM/1000 + 1) x 10
```

**Rotational Dynamics:**
```
alpha = (T_motor - T_load - T_damping) / I
RPM_new = RPM_old + alpha x dt
```

**Pressure Generation:**
```
dP/dt = (RPM/500) x efficiency_comp x 2 - leak_rate x P
```

**Vibration:**
```
V_total = V_base + (RPM/1000)^1.5 x 15 + imbalance_factors
```

## Usage Examples

### Example 1: Normal Operation
```python
from machine_engine import MachineEngine

engine = MachineEngine()
engine.set_params(voltage=170, rotation=450, pressure=100, vibration=40)

# Run simulation
data = engine.tick()
print(f"Voltage: {data['volt']}V")
print(f"Rotation: {data['rotate']} RPM")
print(f"Pressure: {data['pressure']} bar")
print(f"Vibration: {data['vibration']} mm/s")
```

### Example 2: High Load Test
```python
engine.set_params(voltage=200, rotation=1500, pressure=180, vibration=40)
data = engine.tick()
# Observe higher torque, temperature, and vibration
```

### Example 3: Monitor Over Time
```python
import time

for i in range(10):
    data = engine.tick()
    print(f"t={i}s: RPM={data['rotate']:.0f}, P={data['pressure']:.1f}bar")
    time.sleep(1)
```

## Telemetry Data

Each `tick()` returns:

```python
{
    "timestamp": 1778049828.23,      # Unix timestamp
    "volt": 172.03,                  # Voltage (V)
    "rotate": 450.15,                # Rotation (RPM)
    "pressure": 101.62,              # Pressure (bar)
    "vibration": 42.35,              # Vibration (mm/s)
    "is_anomaly": False,             # Anomaly flag
    "temperature": 45.2,             # Motor temp (C)
    "wear": 2.5,                     # Wear percentage
    "motor_torque": 125.5,           # Motor torque (Nm)
    "load_torque": 45.2              # Load torque (Nm)
}
```

## Anomaly Detection

The system automatically detects dangerous conditions:

| Condition | Threshold | Risk |
|-----------|-----------|------|
| Overvoltage | >250V | Electrical damage |
| Undervoltage | <100V | Stall condition |
| Stall | <100 RPM | Motor damage |
| Overspeed | >2500 RPM | Mechanical failure |
| Overpressure | >200 bar | Tank rupture |
| Excessive vibration | >80 mm/s | Bearing damage |
| Overheating | >120C | Thermal damage |

## Customization

### Modify Physical Constants

Edit `machine_engine.py`:

```python
self.motor_efficiency = 0.85       # Motor efficiency (0-1)
self.compressor_efficiency = 0.75  # Compression efficiency (0-1)
self.rotor_inertia = 2.5          # Rotational inertia (kg x m^2)
self.bearing_damping = 0.15       # Bearing damping coefficient
self.leak_rate = 0.02             # Pressure leak rate
```

### Add Custom Sensors

Extend the `tick()` method:

```python
def tick(self):
    # ... existing code ...
    
    return {
        # ... existing sensors ...
        "oil_pressure": self.calculate_oil_pressure(),
        "flow_rate": self.calculate_flow_rate(),
        "power_consumption": self.actual_voltage * self.calculate_current()
    }
```

### Change UI Appearance

Edit `ui.html` CSS variables:

```css
:root {
    --accent: #007acc;      /* Primary color */
    --danger: #e06c75;      /* Danger color */
    --warning: #d19a66;     /* Warning color */
    --success: #98c379;     /* Success color */
}
```

## Learning Outcomes

This simulation teaches:

1. Electromechanical Systems - How electrical and mechanical systems interact
2. Control Theory - PID control, setpoints, and feedback
3. Thermodynamics - Heat generation and cooling
4. Vibration Analysis - Sources and effects of vibration
5. Predictive Maintenance - How wear and operating conditions affect equipment life

## Comparison to Other Tools

| Feature | This Simulator | Simulink | AutoCAD | SolidWorks |
|---------|---------------|----------|---------|------------|
| Physics simulation | Yes | Yes | No | Yes |
| Real-time control | Yes | Partial | No | Partial |
| Web-based | Yes | No | No | No |
| 3D CAD modeling | Partial | No | Yes | Yes |
| Free & open source | Yes | No | No | No |
| Easy to customize | Yes | Partial | No | No |

## Future Enhancements

- PID controller implementation
- Multi-stage compression
- Oil system simulation
- Acoustic/noise modeling
- 3D visualization with Three.js
- Machine learning integration
- Historical data logging
- Export to Simulink format

## License

This project is open source. Feel free to modify and extend it for your needs.

## Contributing

Contributions welcome! Areas for improvement:
- More realistic physics models
- Additional sensor types
- Better visualization
- Performance optimization
- Documentation improvements

---

**Happy Simulating!**

For questions or issues, please refer to the codebase.
