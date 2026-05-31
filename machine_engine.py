import time
import random
import math

class MachineEngine:
    """
    Industrial Rotary Screw Air Compressor Simulation
    
    Based on real-world specifications:
    - Atlas Copco GA37 / Airpol 37 class machine
    - 37 kW, 380V/3-phase/50Hz, 4-pole induction motor
    - Direct drive, oil-injected, single stage
    - Discharge pressure: 7-13 bar (typical industrial)
    - Motor speed: 1460 RPM (4-pole, 50Hz, with slip)
    - Vibration per ISO 10816-3, Class II (15-75 kW)
    
    The 4 parameters represent:
    - Voltage: Supply voltage to motor (380V nominal, 3-phase)
    - Rotation: Motor/airend speed (RPM)
    - Pressure: Discharge air pressure (bar gauge)
    - Vibration: Bearing housing velocity (mm/s RMS, ISO 10816)
    """
    
    def __init__(self):
        # ══════════════════════════════════════════════════════════════
        # REAL MACHINE SPECIFICATIONS (37 kW Screw Compressor)
        # ══════════════════════════════════════════════════════════════
        
        # -- Motor Nameplate Data --
        self.motor_power_kw: float = 37.0         # Rated power (kW)
        self.motor_rated_voltage: float = 380.0   # Rated line voltage (V), 3-phase
        self.motor_rated_current: float = 68.0    # Rated current (A)
        self.motor_rated_speed: float = 1460.0    # Rated speed (RPM) - 4 pole, 50Hz
        self.motor_sync_speed: float = 1500.0     # Synchronous speed (RPM)
        self.motor_poles: int = 4
        self.motor_efficiency: float = 0.935      # IE3 efficiency at full load
        self.motor_power_factor: float = 0.86     # Power factor at full load
        self.motor_slip_rated: float = 0.027      # Rated slip (1500-1460)/1500
        
        # -- Compressor Airend Data --
        self.airend_displacement: float = 0.113   # m³/rev (6.8 m³/min at 1460 RPM / 60)
        self.rated_flow: float = 6.8              # m³/min FAD at 7 bar
        self.volumetric_efficiency: float = 0.92
        self.mechanical_efficiency: float = 0.90
        
        # -- System Data --
        self.receiver_volume: float = 0.5         # m³ (500L receiver tank)
        self.rated_pressure: float = 8.0          # bar (rated discharge)
        self.max_pressure: float = 13.0           # bar (safety valve setting)
        self.unload_pressure: float = 8.5         # bar (unload setpoint)
        self.load_pressure: float = 7.5           # bar (load setpoint)
        
        # -- Mechanical Data --
        self.rotor_inertia: float = 2.5           # kg·m² (motor + airend + coupling)
        self.bearing_friction_coeff: float = 0.003  # Nm per RPM
        
        # ══════════════════════════════════════════════════════════════
        # USER SETPOINTS (What the sliders control)
        # ══════════════════════════════════════════════════════════════
        self.voltage_setpoint: float = 380.0      # V (nominal)
        self.rotation_setpoint: float = 1460.0    # RPM (rated)
        self.pressure_setpoint: float = 8.0       # bar (normal operating)
        self.vibration_setpoint: float = 2.5      # mm/s RMS (good condition)
        
        # ══════════════════════════════════════════════════════════════
        # ACTUAL PHYSICAL STATE
        # ══════════════════════════════════════════════════════════════
        self.actual_voltage: float = 380.0
        self.actual_rotation: float = 1460.0
        self.actual_pressure: float = 8.0
        self.actual_vibration: float = 2.5
        
        # ══════════════════════════════════════════════════════════════
        # SECONDARY STATE
        # ══════════════════════════════════════════════════════════════
        self.temperature: float = 35.0            # Discharge air temp (°C)
        self.oil_temperature: float = 45.0        # Oil temperature (°C)
        self.wear_factor: float = 0.0             # 0-1 (bearing condition)
        self.running_hours: float = 0.0           # Total hours
        
        # ══════════════════════════════════════════════════════════════
        # OPERATING LIMITS (for UI sliders)
        # ══════════════════════════════════════════════════════════════
        self.max_voltage: float = 440.0           # Max supply voltage
        self.max_rotation: float = 3000.0         # Max RPM (VFD range)
        self.max_vibration: float = 15.0          # mm/s (way beyond danger)
        
        # -- Internal --
        self._last_tick: float = time.time()

    def set_params(self, voltage: float = None, rotation: float = None,
                   pressure: float = None, vibration: float = None):
        """Update setpoints from UI sliders."""
        if voltage is not None:
            self.voltage_setpoint = max(0.0, min(float(voltage), self.max_voltage))
        if rotation is not None:
            self.rotation_setpoint = max(0.0, min(float(rotation), self.max_rotation))
        if pressure is not None:
            self.pressure_setpoint = max(0.0, min(float(pressure), self.max_pressure))
        if vibration is not None:
            self.vibration_setpoint = max(0.0, min(float(vibration), self.max_vibration))

    def _motor_torque(self, voltage: float, rpm: float) -> float:
        """
        Induction motor torque-speed curve (simplified Kloss formula).
        
        Real behavior:
        - Torque is proportional to V²
        - At rated slip, produces rated torque
        - Breakdown torque is ~2.5x rated torque
        - Below sync speed: motoring. Above: generating (not modeled)
        """
        if voltage < 10.0:
            return 0.0
        
        # Rated torque: P = T * omega => T = P / omega
        omega_rated = self.motor_rated_speed * 2.0 * math.pi / 60.0
        T_rated = (self.motor_power_kw * 1000.0) / omega_rated  # ~242 Nm
        
        # Voltage scaling: torque proportional to (V/V_rated)²
        voltage_factor = (voltage / self.motor_rated_voltage) ** 2
        
        # Slip-based torque (simplified Kloss equation)
        # s = (sync_speed - rpm) / sync_speed
        sync_speed = self.motor_sync_speed * (voltage / self.motor_rated_voltage)
        if sync_speed < 1.0:
            return 0.0
        
        slip = (sync_speed - rpm) / sync_speed
        slip = max(0.0, min(1.0, slip))  # Clamp 0 to 1
        
        # Kloss formula: T/T_max = 2 / (s/s_max + s_max/s)
        s_rated = self.motor_slip_rated
        s_breakdown = s_rated * 2.5  # Breakdown slip
        
        if slip < 0.001:
            return 0.0
        
        # Simplified: linear region (slip < breakdown)
        if slip <= s_breakdown:
            torque = T_rated * (slip / s_rated) * voltage_factor
        else:
            # Beyond breakdown: torque drops
            torque = T_rated * 2.5 * (s_breakdown / slip) * voltage_factor
        
        # Cap at breakdown torque
        torque = min(torque, T_rated * 2.5 * voltage_factor)
        
        return max(0.0, torque * self.motor_efficiency)

    def _compressor_load(self, pressure: float, rpm: float) -> float:
        """
        Screw compressor load torque.
        
        For a positive displacement compressor:
        Power_compression = V_dot * P_discharge * ln(P_d/P_s) (isothermal)
        
        In practice, torque is nearly constant for a given pressure
        (characteristic of displacement machines).
        T_load = (displacement * delta_P) / (2*pi*eta_mech)
        """
        if rpm < 10.0:
            return 0.0
        
        # Pressure difference (discharge - suction in Pa)
        # Suction = atmospheric = 1.013 bar
        p_suction = 1.013  # bar
        delta_p = max(0.0, pressure - p_suction) * 1e5  # Pa
        
        # Displacement per revolution (m³/rev)
        # Real: 6.8 m³/min / 1460 RPM = 0.00466 m³/rev
        disp_per_rev = self.rated_flow / (self.motor_rated_speed * 60.0)  # m³/rev... wait
        # Actually: rated_flow = 6.8 m³/min, at 1460 RPM
        # disp_per_rev = 6.8 / 1460 = 0.00466 m³/rev
        disp_per_rev = self.rated_flow / self.motor_rated_speed  # m³/min per RPM = m³/rev * 1/min... 
        # Correct: flow = RPM * displacement => displacement = flow/RPM
        # 6.8 m³/min = 1460 rev/min * d => d = 6.8/1460 = 0.00466 m³/rev
        disp_per_rev = self.rated_flow / (self.motor_rated_speed)  # 0.00466 m³/rev (per min basis)
        
        # Torque = displacement_per_rev * delta_P / (2*pi * eta_mech)
        # But displacement here is in m³/min per RPM, need m³/rev
        # d = 6.8 m³/min / 1460 rev/min = 0.004658 m³/rev
        d = 0.004658  # m³/rev
        
        torque = d * delta_p / (2.0 * math.pi * self.mechanical_efficiency)
        
        # Scale with RPM ratio (at lower speeds, volumetric efficiency drops)
        rpm_ratio = rpm / self.motor_rated_speed
        vol_eff = self.volumetric_efficiency * min(1.0, 0.7 + 0.3 * rpm_ratio)
        
        return max(0.0, torque * vol_eff)

    def _pressure_dynamics(self, rpm: float, current_pressure: float, dt: float) -> float:
        """
        Receiver tank pressure dynamics.
        
        dP/dt = (mass_flow_in - mass_flow_out) * R*T / (V * M)
        
        Simplified using ideal gas:
        dP/dt = (Q_in - Q_out) * P_atm / V_receiver
        
        Load/Unload control:
        - Below load_pressure: full load (suction valve open)
        - Above unload_pressure: unload (suction valve closed)
        - Between: modulating
        """
        # Air demand (simulated plant consumption) - proportional to pressure
        # At 8 bar, typical plant uses about 80% of compressor capacity
        air_demand = self.rated_flow * 0.75 * (current_pressure / self.rated_pressure)  # m³/min
        
        # Compressor output (proportional to RPM)
        if rpm < 50.0:
            compressor_output = 0.0
        else:
            compressor_output = self.rated_flow * (rpm / self.motor_rated_speed) * self.volumetric_efficiency
        
        # Load/Unload control (suction valve modulation)
        load_factor = 1.0
        if current_pressure > self.pressure_setpoint * 1.06:
            load_factor = 0.0  # Fully unloaded
        elif current_pressure > self.pressure_setpoint * 1.0:
            # Modulating
            excess = (current_pressure - self.pressure_setpoint) / (self.pressure_setpoint * 0.06)
            load_factor = max(0.0, 1.0 - excess)
        
        effective_output = compressor_output * load_factor
        
        # Net flow into receiver (m³/min)
        net_flow = effective_output - air_demand
        
        # Pressure change: dP = net_flow * P_atm / V_receiver
        # Convert m³/min to m³/s
        net_flow_per_sec = net_flow / 60.0
        
        # dP (bar) = net_flow (m³/s) * 1.013 (bar) / V_receiver (m³)
        dp = net_flow_per_sec * 1.013 / self.receiver_volume * dt
        
        return dp

    def _vibration_model(self, rpm: float, pressure: float, voltage: float) -> float:
        """
        Vibration model per ISO 10816-3 principles.
        
        Real vibration sources in a screw compressor:
        1. Residual imbalance (proportional to RPM²)
        2. Misalignment (1x and 2x RPM)
        3. Bearing condition (broadband, increases with wear)
        4. Pressure pulsation (at meshing frequency)
        5. Electrical (2x line frequency = 100Hz)
        
        ISO 10816-3 Class II (15-75 kW, rigid foundation):
        Zone A (new): 0 - 2.3 mm/s
        Zone B (acceptable): 2.3 - 4.5 mm/s
        Zone C (alarm): 4.5 - 7.1 mm/s
        Zone D (danger): > 7.1 mm/s
        """
        # Base vibration from mechanical condition (setpoint = machine health)
        # setpoint represents the overall machine condition
        base = self.vibration_setpoint * 0.6
        
        # RPM contribution (imbalance force = m*r*omega²)
        # At rated speed (1460 RPM), a well-balanced machine adds ~1.0 mm/s
        rpm_ratio = rpm / self.motor_rated_speed
        imbalance = rpm_ratio ** 2 * 1.2
        
        # Pressure pulsation (meshing frequency vibration)
        # Higher pressure = more pulsation energy
        pressure_ratio = pressure / self.rated_pressure if self.rated_pressure > 0 else 0
        pulsation = pressure_ratio * 0.4
        
        # Voltage imbalance (causes 2x electrical vibration)
        v_deviation = abs(voltage - self.motor_rated_voltage) / self.motor_rated_voltage
        electrical = v_deviation * 3.0  # Significant at >5% voltage deviation
        
        # Bearing wear contribution
        wear_vib = self.wear_factor * 8.0  # Worn bearings can add up to 8 mm/s
        
        # Total vibration (RMS combination)
        total = math.sqrt(base**2 + imbalance**2 + pulsation**2 + electrical**2) + wear_vib
        
        return max(0.1, total)

    def _temperature_model(self, voltage: float, rpm: float, pressure: float, dt: float):
        """
        Discharge air temperature model.
        
        Real screw compressor:
        - Compression heats air: T2 = T1 * (P2/P1)^((gamma-1)/gamma)
        - Oil injection limits temperature to ~80-100°C
        - Aftercooler brings it down to ambient + 10-15°C
        - Oil temp typically 60-90°C
        """
        ambient = 25.0
        
        # Compression discharge temp (before oil mixing)
        gamma = 1.4  # Air
        if pressure > 1.0:
            p_ratio = pressure / 1.013
            T_adiabatic = (ambient + 273.15) * (p_ratio ** ((gamma - 1) / gamma)) - 273.15
        else:
            T_adiabatic = ambient
        
        # Oil injection limits max temp (oil absorbs heat)
        # Typical oil-injected discharge: 75-95°C
        T_target = min(T_adiabatic, 85.0 + (rpm / self.motor_rated_speed - 1.0) * 20.0)
        
        # After aftercooler: ambient + 10-15°C approach
        T_aftercooler = ambient + 12.0 + (T_target - ambient) * 0.1
        
        # First-order response
        tau = 30.0  # Thermal time constant (seconds)
        alpha = dt / (tau + dt)
        self.temperature = self.temperature + alpha * (T_aftercooler - self.temperature)
        self.temperature = max(ambient, min(120.0, self.temperature))
        
        # Oil temperature (higher than air discharge)
        T_oil_target = T_target * 0.9 + ambient * 0.1
        self.oil_temperature = self.oil_temperature + alpha * (T_oil_target - self.oil_temperature)

    def _wear_model(self, rpm: float, vibration: float, temperature: float, dt: float):
        """Bearing wear accumulation (very slow)."""
        # Wear accelerates with high vibration and temperature
        vib_factor = max(0, vibration - 2.0) / 5.0  # Above 2 mm/s starts wearing
        temp_factor = max(0, (self.oil_temperature - 70.0) / 30.0)  # Above 70°C
        speed_factor = rpm / self.motor_rated_speed
        
        rate = speed_factor * (1.0 + vib_factor + temp_factor) * 0.000002 * dt
        self.wear_factor = min(1.0, self.wear_factor + rate)
        self.running_hours += dt / 3600.0

    def tick(self) -> dict:
        """Advance simulation one time step. Returns sensor data."""
        now = time.time()
        dt = now - self._last_tick
        dt = max(0.05, min(2.0, dt))
        self._last_tick = now

        # Sub-step for numerical stability
        num_steps = 10
        sub_dt = dt / num_steps

        for _ in range(num_steps):
            # 1. VOLTAGE (fast electrical response, tau ~ 0.1s)
            v_tau = 0.1
            v_alpha = sub_dt / (v_tau + sub_dt)
            self.actual_voltage += v_alpha * (self.voltage_setpoint - self.actual_voltage)

            # 2. ROTATION (electromechanical dynamics)
            T_motor = self._motor_torque(self.actual_voltage, self.actual_rotation)
            T_load = self._compressor_load(self.actual_pressure, self.actual_rotation)
            T_friction = self.bearing_friction_coeff * self.actual_rotation
            T_net = T_motor - T_load - T_friction

            # Newton's 2nd law: I * alpha = T_net
            alpha_rad = T_net / self.rotor_inertia  # rad/s²
            alpha_rpm = alpha_rad * 60.0 / (2.0 * math.pi)  # RPM/s

            # VFD speed control (if setpoint differs from natural speed)
            # VFD adjusts frequency to target speed
            governor = (self.rotation_setpoint - self.actual_rotation) * 8.0  # RPM/s per RPM error

            self.actual_rotation += (alpha_rpm + governor) * sub_dt
            self.actual_rotation = max(0.0, min(self.max_rotation, self.actual_rotation))

            # 3. PRESSURE (thermodynamic, slower response)
            dp = self._pressure_dynamics(self.actual_rotation, self.actual_pressure, sub_dt)
            self.actual_pressure += dp
            self.actual_pressure = max(0.0, min(self.max_pressure, self.actual_pressure))

        # 4. VIBRATION (instantaneous mechanical state)
        self.actual_vibration = self._vibration_model(
            self.actual_rotation, self.actual_pressure, self.actual_voltage
        )

        # 5. TEMPERATURE (slow thermal response)
        self._temperature_model(self.actual_voltage, self.actual_rotation, self.actual_pressure, dt)

        # 6. WEAR
        self._wear_model(self.actual_rotation, self.actual_vibration, self.temperature, dt)

        # ═══ SENSOR OUTPUTS (with realistic instrument noise) ═══
        # Voltage sensor: ±2V accuracy (typical power analyzer)
        out_volt = max(0.0, random.gauss(self.actual_voltage, 2.0))
        # Tachometer: ±1 RPM (optical encoder)
        out_rotate = max(0.0, random.gauss(self.actual_rotation, 1.0))
        # Pressure transducer: ±0.05 bar (industrial grade)
        out_press = max(0.0, random.gauss(self.actual_pressure, 0.05))
        # Accelerometer: ±0.1 mm/s (ICP vibration sensor)
        out_vib = max(0.0, random.gauss(self.actual_vibration, 0.1))

        # Anomaly detection (based on real alarm thresholds)
        is_anomaly = (
            out_volt > 420.0 or           # >10% overvoltage
            out_volt < 342.0 or           # >10% undervoltage
            out_rotate < 200.0 or         # Stall
            out_rotate > 1600.0 or        # Overspeed (for fixed speed)
            out_press > 10.0 or           # Overpressure
            out_vib > 7.1 or             # ISO 10816 Zone D
            self.temperature > 105.0      # High discharge temp
        )

        return {
            "timestamp": round(now, 3),
            "volt": round(out_volt, 2),
            "rotate": round(out_rotate, 2),
            "pressure": round(out_press, 2),
            "vibration": round(out_vib, 2),
            "is_anomaly": is_anomaly,
            "temperature": round(self.temperature, 1),
            "wear": round(self.wear_factor * 100, 2),
            "motor_torque": round(T_motor, 1),
            "load_torque": round(T_load, 1),
        }

    def get_state(self) -> dict:
        """Return current state."""
        return {
            "volt": self.actual_voltage,
            "rotate": self.actual_rotation,
            "pressure": self.actual_pressure,
            "vibration": self.actual_vibration,
            "temperature": self.temperature,
            "wear": self.wear_factor * 100,
        }

    def reset(self):
        """Reset to initial conditions."""
        self.actual_voltage = self.voltage_setpoint
        self.actual_rotation = self.rotation_setpoint
        self.actual_pressure = self.pressure_setpoint
        self.actual_vibration = self.vibration_setpoint
        self.temperature = 35.0
        self.oil_temperature = 45.0
        self.wear_factor = 0.0
        self._last_tick = time.time()
