# Component Lifecycle Tracking Guide

## ✅ New Features Added

### **Battery Cycle Tracking**
- Track charge/discharge cycles for each battery
- Monitor battery health degradation
- Get alerts when batteries approach cycle limits

### **Component Usage Tracking**
- Track flight hours for motors, propellers, ESCs
- Monitor component wear over time
- Automatic usage increment after each flight

### **Lifecycle Management**
- Set replacement thresholds per component
- Automatic health percentage calculation
- Maintenance alerts at 25% and 10% health remaining

---

## 📊 Default Component Lifecycles

| Component | Max Flight Hours | Max Flight Count | Max Cycles | Notes |
|-----------|------------------|------------------|------------|-------|
| **Battery** | 150 hours | 300 flights | 300 cycles | Critical for safety |
| **Motor** | 300 hours | 1000 flights | N/A | Check bearings regularly |
| **Propeller** | 50 hours | 200 flights | N/A | Replace if cracked |
| **ESC** | 500 hours | 1000 flights | N/A | Rarely fail |

*Note: These are default recommendations. You can customize per component.*

---

## 🚀 How to Use

### **1. Register Components**

After uploading your first flight:

1. Go to **Drones** page
2. Click on your drone
3. Click **"Components"** button
4. Click **"Register Component"**
5. Fill in details:
   - **Type**: Battery, Motor, Propeller, or ESC
   - **Name**: e.g., "Battery-001", "Motor Front Left"
   - **Serial Number**: Optional but recommended
   - **Position**: e.g., "front_left", "rear_right"

### **2. Automatic Tracking**

Once registered, components automatically track:
- **Flight hours** - Incremented after each flight
- **Flight count** - Number of flights flown
- **Battery cycles** - Each flight counts as 1 cycle for batteries

### **3. Monitor Health**

Each component shows:
- **Health percentage** (100% = new, 0% = overdue)
- **Status**: good → attention → replace_soon → overdue
- **Visual health bar** (green → yellow → red)
- **Usage stats** vs. limits

### **4. Get Alerts**

Automatic alerts generated when:
- **25% health**: "Component should be replaced soon"
- **10% health**: "Component is OVERDUE for replacement"

Alerts appear in:
- Maintenance page (with component lifecycle type)
- Drone detail page

### **5. Replace Components**

When it's time to replace:

1. Go to drone's **Components** page
2. Find the component
3. Click **"Mark as Replaced"**
4. Add notes (optional)
5. System creates:
   - New component entry (100% health)
   - Maintenance log with old usage stats
   - Auto-resolves lifecycle alerts

---

## 🔧 API Endpoints

### **Register Component**
```http
POST /api/components/register?drone_id={id}
{
  "component_type": "battery",
  "component_name": "Battery-001",
  "serial_number": "BAT-SN-12345",
  "position": "main"
}
```

### **Get Drone Components**
```http
GET /api/components/drone/{drone_id}?active_only=true
```

### **Get Component Details**
```http
GET /api/components/{component_id}
```

### **Replace Component**
```http
POST /api/components/{component_id}/replace
{
  "new_serial_number": "BAT-SN-67890",
  "notes": "Replaced due to reduced capacity",
  "performed_by": "Tech John",
  "cost": 89.99
}
```

### **Update Component**
```http
PUT /api/components/{component_id}
{
  "max_cycles": 400,
  "notes": "High-capacity battery"
}
```

### **Fleet Summary**
```http
GET /api/components/fleet/summary
```

---

## 📈 Component Health Calculation

Health is calculated as:

```
Health% = 100% - (Worst Case Usage%)

Where Usage% = max of:
  - (total_flight_hours / max_flight_hours) × 100
  - (total_flight_count / max_flight_count) × 100
  - (total_cycles / max_cycles) × 100
```

**Example:**
```
Battery-001:
  - 120 hours / 150 max = 80% usage
  - 250 flights / 300 max = 83% usage
  - 280 cycles / 300 max = 93% usage ← Worst case
  
Health = 100% - 93% = 7%
Status = "overdue" (health < 10%)
```

---

## 🎨 UI Components

### **Components Page** (`/drones/:id/components`)

Shows all registered components with:
- Component icon (battery, motor, propeller, ESC)
- Health bar (visual indicator)
- Usage statistics (hours, flights, cycles)
- Status badge (color-coded)
- Replace button

### **Register Modal**

Simple form to add new components:
- Dropdown for component type
- Text inputs for name, serial, position
- Auto-applies default lifecycle limits

### **Health Status Colors**

- 🟢 **Good** (>50% health): Green
- 🔵 **Attention** (25-50% health): Blue
- 🟡 **Replace Soon** (10-25% health): Yellow
- 🔴 **Overdue** (<10% health): Red
- ⚫ **Replaced** (inactive): Gray

---

## 💾 Database Schema

### **components Table**

```sql
CREATE TABLE components (
    id INTEGER PRIMARY KEY,
    drone_id INTEGER NOT NULL,
    component_type VARCHAR(50),  -- battery, motor, propeller, esc
    component_name VARCHAR(100),
    serial_number VARCHAR(100),
    position VARCHAR(50),
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    installed_date TIMESTAMP,
    removed_date TIMESTAMP,
    
    -- Usage tracking
    total_flight_hours FLOAT DEFAULT 0.0,
    total_flight_count INTEGER DEFAULT 0,
    total_cycles INTEGER DEFAULT 0,  -- Batteries only
    
    -- Limits
    max_flight_hours FLOAT,
    max_flight_count INTEGER,
    max_cycles INTEGER,
    
    -- Health
    status VARCHAR(20),  -- good, attention, replace_soon, overdue
    health_percentage FLOAT,
    
    -- Maintenance
    last_maintenance_date TIMESTAMP,
    notes TEXT,
    
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    
    FOREIGN KEY (drone_id) REFERENCES drones(id)
);
```

### **component_maintenance Table**

```sql
CREATE TABLE component_maintenance (
    id INTEGER PRIMARY KEY,
    component_id INTEGER NOT NULL,
    maintenance_type VARCHAR(50),  -- replaced, inspected, repaired
    maintenance_date TIMESTAMP,
    performed_by VARCHAR(100),
    notes TEXT,
    
    -- Usage at time of maintenance
    flight_hours_at_maintenance FLOAT,
    flight_count_at_maintenance INTEGER,
    cycles_at_maintenance INTEGER,
    
    -- Replacement tracking
    new_component_id INTEGER,  -- Links to new component if replaced
    cost FLOAT,
    
    created_at TIMESTAMP,
    
    FOREIGN KEY (component_id) REFERENCES components(id)
);
```

---

## 🔄 Automatic Updates

### **After Flight Upload**

1. Flight record created with duration
2. **Telemetry Service** calls **Component Service**
3. Component Service:
   - Finds all active components for that drone
   - Increments `total_flight_hours` (duration / 3600)
   - Increments `total_flight_count` (+1)
   - For batteries: increments `total_cycles` (+1)
   - Recalculates health percentage
   - Updates status based on health
   - Checks if alerts needed

### **Alert Generation**

When health drops below thresholds:
- **25%**: Creates **warning** alert
- **10%**: Creates **critical** alert

Alert includes:
- Component name and type
- Current health percentage
- Usage statistics
- Specific maintenance recommendation

---

## 📝 Maintenance Logs

Every replacement creates a log entry with:
- **What**: Component type and name
- **When**: Date/time of replacement
- **Who**: Person who performed replacement (optional)
- **Usage**: Hours, flights, cycles at replacement
- **Cost**: Replacement cost (optional)
- **Link**: References both old and new component IDs

View history:
```http
GET /api/components/{component_id}
```

Returns component details + full maintenance history.

---

## 🎯 Use Cases

### **Battery Management**

Track multiple batteries per drone:
```
Drone-001
├── Battery-A: 280 cycles, 7% health, OVERDUE
├── Battery-B: 150 cycles, 50% health, GOOD
└── Battery-C: 75 cycles, 75% health, GOOD
```

Rotate batteries to even wear, replace when overdue.

### **Motor Wear Tracking**

Individual motor hour tracking:
```
Drone-001
├── Motor FL: 320h, 6% health, OVERDUE
├── Motor FR: 285h, 28% health, REPLACE SOON
├── Motor RL: 290h, 24% health, REPLACE SOON
└── Motor RR: 295h, 20% health, REPLACE SOON
```

Identify motors wearing faster (imbalance issues).

### **Propeller Replacement**

Short lifecycle components:
```
Propeller Set-1: 48h, 4% health, REPLACE SOON
```

Replace full set every ~50 hours or 200 flights.

### **Fleet-Wide View**

```
GET /api/components/fleet/summary

{
  "total_components": 32,
  "by_type": {
    "battery": 8,
    "motor": 16,
    "propeller": 4,
    "esc": 4
  },
  "by_status": {
    "good": 20,
    "attention": 5,
    "replace_soon": 4,
    "overdue": 3
  },
  "components_needing_attention": [...]
}
```

---

## 🚨 Important Notes

1. **Manual Registration Required**: Components don't auto-register. You must manually add them after first flight.

2. **Retrospective Tracking**: Components only track flights AFTER registration. Historical flights don't count.

3. **Battery Cycles = Flights**: Each flight counts as 1 battery cycle (simplified model).

4. **Cascade Delete**: Deleting a drone deletes all its components.

5. **Inactive Components**: Replaced components stay in database (is_active=false) for history.

---

## 💡 Tips & Best Practices

### **Registration Strategy**

1. **Day 1**: Upload first flight
2. **Day 2**: Register all critical components (batteries, motors)
3. **Ongoing**: Components auto-update with each new flight

### **Component Naming**

Use consistent naming:
- **Batteries**: "Battery-001", "Battery-002", etc.
- **Motors**: "Motor FL", "Motor FR", "Motor RL", "Motor RR"
- **Propellers**: "Propeller Set-1", "Propeller Set-2"
- **ESCs**: "ESC-1", "ESC-2", etc.

### **Custom Limits**

Adjust limits based on:
- Component quality (premium vs. budget)
- Operating conditions (aggressive vs. gentle flying)
- Manufacturer recommendations

```http
PUT /api/components/1
{
  "max_cycles": 500,  // High-quality battery
  "notes": "Premium LiPo, rated 500 cycles"
}
```

### **Proactive Replacement**

Don't wait for "overdue":
- **Replace Soon** (10-25% health): Order replacement
- **Attention** (25-50% health): Plan maintenance window
- **Good** (>50% health): Monitor trends

---

## 🎉 Benefits

✅ **Never miss a replacement** - Automatic alerts
✅ **Optimize costs** - Replace only when needed
✅ **Improve safety** - Track critical components
✅ **Maintenance history** - Audit trail for all replacements
✅ **Fleet insights** - See which components fail first
✅ **Data-driven decisions** - Real usage vs. estimates

---

**Feature is now fully implemented and ready to use!** 🚁🔋⚙️
