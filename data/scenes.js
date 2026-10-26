// Written by scripts/collect_scenes.py: the scenes of the gallery and their 10k-iteration metrics.
window.TFDSFM_SCENES = {
 "teaser": [
  "eth3d_courtyard",
  "mip360_room",
  "dtu_scan45",
  "imc_florence_cathedral_side"
 ],
 "datasets": [
  {
   "key": "dtu",
   "name": "DTU",
   "note": "The 15 scans of the SPARF protocol, 49 images each.",
   "scenes": [
    {
     "id": "dtu_scan8",
     "name": "scan8",
     "bag": null,
     "rra5": 100.0,
     "rta5": 69.73,
     "images": 49,
     "mirror": false
    },
    {
     "id": "dtu_scan21",
     "name": "scan21",
     "bag": null,
     "rra5": 100.0,
     "rta5": 88.61,
     "images": 49,
     "mirror": false
    },
    {
     "id": "dtu_scan30",
     "name": "scan30",
     "bag": null,
     "rra5": 75.6,
     "rta5": 13.35,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan31",
     "name": "scan31",
     "bag": null,
     "rra5": 100.0,
     "rta5": 97.02,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan34",
     "name": "scan34",
     "bag": null,
     "rra5": 100.0,
     "rta5": 74.15,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan38",
     "name": "scan38",
     "bag": null,
     "rra5": 100.0,
     "rta5": 88.35,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan40",
     "name": "scan40",
     "bag": null,
     "rra5": 100.0,
     "rta5": 57.48,
     "images": 49,
     "mirror": false
    },
    {
     "id": "dtu_scan41",
     "name": "scan41",
     "bag": null,
     "rra5": 100.0,
     "rta5": 56.29,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan45",
     "name": "scan45",
     "bag": null,
     "rra5": 100.0,
     "rta5": 57.57,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan55",
     "name": "scan55",
     "bag": null,
     "rra5": 100.0,
     "rta5": 97.62,
     "images": 49,
     "mirror": false
    },
    {
     "id": "dtu_scan63",
     "name": "scan63",
     "bag": null,
     "rra5": 100.0,
     "rta5": 64.8,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan82",
     "name": "scan82",
     "bag": null,
     "rra5": 100.0,
     "rta5": 58.25,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan103",
     "name": "scan103",
     "bag": null,
     "rra5": 100.0,
     "rta5": 90.39,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan110",
     "name": "scan110",
     "bag": null,
     "rra5": 100.0,
     "rta5": 83.93,
     "images": 49,
     "mirror": true
    },
    {
     "id": "dtu_scan114",
     "name": "scan114",
     "bag": null,
     "rra5": 100.0,
     "rta5": 85.88,
     "images": 49,
     "mirror": true
    }
   ]
  },
  {
   "key": "mip360",
   "name": "Mip-NeRF 360",
   "note": "All 7 scenes of the benchmark.",
   "scenes": [
    {
     "id": "mip360_bicycle",
     "name": "bicycle",
     "bag": null,
     "rra5": 100.0,
     "rta5": 99.62,
     "images": 194,
     "mirror": false
    },
    {
     "id": "mip360_bonsai",
     "name": "bonsai",
     "bag": null,
     "rra5": 100.0,
     "rta5": 99.9,
     "images": 292,
     "mirror": false
    },
    {
     "id": "mip360_counter",
     "name": "counter",
     "bag": null,
     "rra5": 100.0,
     "rta5": 99.66,
     "images": 240,
     "mirror": false
    },
    {
     "id": "mip360_garden",
     "name": "garden",
     "bag": null,
     "rra5": 100.0,
     "rta5": 100.0,
     "images": 185,
     "mirror": false
    },
    {
     "id": "mip360_kitchen",
     "name": "kitchen",
     "bag": null,
     "rra5": 100.0,
     "rta5": 99.73,
     "images": 279,
     "mirror": false
    },
    {
     "id": "mip360_room",
     "name": "room",
     "bag": null,
     "rra5": 89.71,
     "rta5": 75.29,
     "images": 311,
     "mirror": false
    },
    {
     "id": "mip360_stump",
     "name": "stump",
     "bag": null,
     "rra5": 100.0,
     "rta5": 95.41,
     "images": 125,
     "mirror": false
    }
   ]
  },
  {
   "key": "eth3d",
   "name": "ETH3D",
   "note": "All 13 high-resolution multi-view training scenes.",
   "scenes": [
    {
     "id": "eth3d_courtyard",
     "name": "courtyard",
     "bag": null,
     "rra5": 100.0,
     "rta5": 97.87,
     "images": 38,
     "mirror": false
    },
    {
     "id": "eth3d_delivery_area",
     "name": "delivery_area",
     "bag": null,
     "rra5": 100.0,
     "rta5": 99.05,
     "images": 44,
     "mirror": false
    },
    {
     "id": "eth3d_electro",
     "name": "electro",
     "bag": null,
     "rra5": 79.29,
     "rta5": 81.21,
     "images": 45,
     "mirror": false
    },
    {
     "id": "eth3d_facade",
     "name": "facade",
     "bag": null,
     "rra5": 100.0,
     "rta5": 99.54,
     "images": 76,
     "mirror": false
    },
    {
     "id": "eth3d_kicker",
     "name": "kicker",
     "bag": null,
     "rra5": 100.0,
     "rta5": 98.92,
     "images": 31,
     "mirror": false
    },
    {
     "id": "eth3d_meadow",
     "name": "meadow",
     "bag": null,
     "rra5": 36.19,
     "rta5": 20.95,
     "images": 15,
     "mirror": false
    },
    {
     "id": "eth3d_office",
     "name": "office",
     "bag": null,
     "rra5": 77.54,
     "rta5": 55.38,
     "images": 26,
     "mirror": false
    },
    {
     "id": "eth3d_pipes",
     "name": "pipes",
     "bag": null,
     "rra5": 100.0,
     "rta5": 100.0,
     "images": 14,
     "mirror": false
    },
    {
     "id": "eth3d_playground",
     "name": "playground",
     "bag": null,
     "rra5": 99.0,
     "rta5": 79.94,
     "images": 38,
     "mirror": false
    },
    {
     "id": "eth3d_relief",
     "name": "relief",
     "bag": null,
     "rra5": 100.0,
     "rta5": 94.62,
     "images": 31,
     "mirror": false
    },
    {
     "id": "eth3d_relief_2",
     "name": "relief_2",
     "bag": null,
     "rra5": 100.0,
     "rta5": 98.06,
     "images": 31,
     "mirror": false
    },
    {
     "id": "eth3d_terrace",
     "name": "terrace",
     "bag": null,
     "rra5": 100.0,
     "rta5": 100.0,
     "images": 23,
     "mirror": false
    },
    {
     "id": "eth3d_terrains",
     "name": "terrains",
     "bag": null,
     "rra5": 100.0,
     "rta5": 71.78,
     "images": 42,
     "mirror": false
    }
   ]
  },
  {
   "key": "imc",
   "name": "IMC2021",
   "note": "All 9 phototourism test scenes. Each is one 25-image bag, the best of up to ten bags (25bag_000 to 25bag_009).",
   "scenes": [
    {
     "id": "imc_british_museum",
     "name": "british_museum",
     "bag": "25bag_002",
     "rra5": 51.67,
     "rta5": 3.0,
     "images": 25,
     "mirror": false
    },
    {
     "id": "imc_florence_cathedral_side",
     "name": "florence_cathedral_side",
     "bag": "25bag_001",
     "rra5": 100.0,
     "rta5": 91.67,
     "images": 25,
     "mirror": false
    },
    {
     "id": "imc_lincoln_memorial_statue",
     "name": "lincoln_memorial_statue",
     "bag": "25bag_009",
     "rra5": 88.0,
     "rta5": 42.0,
     "images": 25,
     "mirror": false
    },
    {
     "id": "imc_london_bridge",
     "name": "london_bridge",
     "bag": "25bag_000",
     "rra5": 91.67,
     "rta5": 24.0,
     "images": 25,
     "mirror": false
    },
    {
     "id": "imc_milan_cathedral",
     "name": "milan_cathedral",
     "bag": "25bag_003",
     "rra5": 75.33,
     "rta5": 23.33,
     "images": 25,
     "mirror": false
    },
    {
     "id": "imc_mount_rushmore",
     "name": "mount_rushmore",
     "bag": "25bag_006",
     "rra5": 77.0,
     "rta5": 4.33,
     "images": 25,
     "mirror": true
    },
    {
     "id": "imc_piazza_san_marco",
     "name": "piazza_san_marco",
     "bag": "25bag_002",
     "rra5": 85.67,
     "rta5": 55.0,
     "images": 25,
     "mirror": false
    },
    {
     "id": "imc_sagrada_familia",
     "name": "sagrada_familia",
     "bag": "25bag_000",
     "rra5": 100.0,
     "rta5": 93.33,
     "images": 25,
     "mirror": false
    },
    {
     "id": "imc_st_pauls_cathedral",
     "name": "st_pauls_cathedral",
     "bag": "25bag_006",
     "rra5": 100.0,
     "rta5": 76.33,
     "images": 25,
     "mirror": false
    }
   ]
  }
 ]
};
