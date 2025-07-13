
PRODUCTS = [
    # SD-WAN
    {
        "sku": "SDW-1000",
        "name": "CloudConnect SD-WAN S",
        "description": "Entry-level SD-WAN appliance for small branches. Supports up to 200Mbps throughput.",
        "use_cases": ["SD-WAN", "Network Security"],
        "price": 1200,
        "volume_discount": {10: 0.05, 20: 0.1}
    },
    {
        "sku": "SDW-2000",
        "name": "CloudConnect SD-WAN M",
        "description": "Mid-range SD-WAN appliance for medium branches. Supports up to 1Gbps throughput and advanced security features.",
        "use_cases": ["SD-WAN", "Network Security", "Access Security"],
        "price": 3500,
        "volume_discount": {10: 0.07, 20: 0.12}
    },

    # Switching
    {
        "sku": "SW-24-POE",
        "name": "NetSwitch 24-Port PoE+",
        "description": "24-port Gigabit PoE+ switch for access points, cameras, and phones. 480W power budget.",
        "use_cases": ["Switching", "Access Security"],
        "price": 800,
        "volume_discount": {10: 0.05, 50: 0.1}
    },
    {
        "sku": "SW-48",
        "name": "NetSwitch 48-Port L3",
        "description": "48-port Gigabit Layer 3 switch for core branch networking.",
        "use_cases": ["Switching"],
        "price": 1500,
        "volume_discount": {10: 0.05, 20: 0.08}
    },

    # Wireless
    {
        "sku": "AP-W6-PRO",
        "name": "AirWave Wi-Fi 6 Pro AP",
        "description": "High-performance Wi-Fi 6 Access Point for dense environments.",
        "use_cases": ["Wireless"],
        "price": 600,
        "volume_discount": {10: 0.05, 50: 0.1}
    },
    {
        "sku": "AP-W6-LR",
        "name": "AirWave Wi-Fi 6 Long-Range AP",
        "description": "Long-range Wi-Fi 6 Access Point for large open spaces.",
        "use_cases": ["Wireless"],
        "price": 750,
        "volume_discount": {10: 0.05, 50: 0.1}
    },

    # Network Security
    {
        "sku": "SEC-FW-100",
        "name": "SecureWall Firewall 100",
        "description": "Next-gen firewall with threat prevention and VPN capabilities.",
        "use_cases": ["Network Security"],
        "price": 2000,
        "volume_discount": {5: 0.05, 10: 0.1}
    },

    # Access Security
    {
        "sku": "SEC-NAC-500",
        "name": "AccessGuard NAC Appliance",
        "description": "Network Access Control solution for 500 users. Enforces security policies on all connected devices.",
        "use_cases": ["Access Security"],
        "price": 4500,
        "volume_discount": {1: 0, 5: 0.05}
    },
    
    # IOT Security
    {
        "sku": "IOT-SEC-GW",
        "name": "IoT-Secure Gateway",
        "description": "Specialized security gateway for IoT device traffic analysis and threat mitigation.",
        "use_cases": ["Network Security", "IOT Security"],
        "price": 1800,
        "volume_discount": {10: 0.05}
    }
]

USE_CASE_MAPPING = {
    # use case 1: SD-WAN routing + switching
    "sdwan_switching": {
        "name": "SD-WAN and Switching Bundle",
        "skus": ["SDW-2000", "SW-48"],
        "description": "A core bundle for reliable branch connectivity and local network management."
    },
    # use case 2: SD-WAN + wireless
    "sdwan_wireless": {
        "name": "SD-WAN and Wireless Bundle",
        "skus": ["SDW-2000", "AP-W6-PRO"],
        "description": "Provides both wired and high-performance wireless connectivity for modern branches."
    },
    # use case 3: SD-WAN + IOT security services
    "sdwan_iot_security": {
        "name": "SD-WAN and IoT Security Bundle",
        "skus": ["SDW-2000", "IOT-SEC-GW"],
        "description": "Securely connect and manage your IoT devices at the branch level."
    }
} 