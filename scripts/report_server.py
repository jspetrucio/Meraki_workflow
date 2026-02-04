#!/usr/bin/env python3
"""
Report Server - Gera relatório HTML visual e serve via localhost
Uso: python report_server.py <path_to_discovery_json>
"""

import json
import os
import sys
import webbrowser
import http.server
import socketserver
import threading
from datetime import datetime
from pathlib import Path

# Porta padrão do servidor
DEFAULT_PORT = 8080

def load_discovery_data(json_path: str) -> dict:
    """Carrega e valida o JSON de discovery"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Garante estrutura mínima
    defaults = {
        'organization': {'name': 'Unknown', 'id': 'N/A'},
        'networks': [],
        'devices': [],
        'configurations': {'vlans': [], 'ssids': [], 'firewall': {'l3_rules': [], 'l7_rules': []}, 'switch_ports': {}},
        'metrics': {'uptime': {}, 'utilization': {}, 'clients': {}},
        'issues': [],
        'suggestions': [],
        'recommended_workflows': [],
        'generated_at': datetime.now().isoformat()
    }
    
    for key, default in defaults.items():
        if key not in data:
            data[key] = default
            
    # Garantir sub-chaves de configurations
    if 'firewall' not in data['configurations']:
        data['configurations']['firewall'] = {'l3_rules': [], 'l7_rules': []}
    
    return data

def calculate_health_score(data: dict) -> int:
    """Calcula score de saúde da rede (0-100)"""
    score = 100
    
    # Penaliza por devices offline
    devices = data.get('devices', [])
    if devices:
        offline = sum(1 for d in devices if d.get('status') == 'offline')
        offline_ratio = offline / len(devices)
        score -= int(offline_ratio * 30)
    
    # Penaliza por issues
    issues = data.get('issues', [])
    for issue in issues:
        severity = issue.get('severity', 'low')
        if severity == 'critical':
            score -= 15
        elif severity == 'high':
            score -= 10
        elif severity == 'medium':
            score -= 5
        else:
            score -= 2
    
    return max(0, min(100, score))

def get_status_color(status: str) -> str:
    """Retorna classe Tailwind para status"""
    colors = {
        'online': 'bg-emerald-500',
        'offline': 'bg-red-500',
        'alerting': 'bg-amber-500',
        'dormant': 'bg-slate-500'
    }
    return colors.get(status, 'bg-slate-500')

def get_severity_color(severity: str) -> str:
    """Retorna classe Tailwind para severidade"""
    colors = {
        'critical': 'bg-red-600 text-white',
        'high': 'bg-orange-500 text-white',
        'medium': 'bg-yellow-500 text-slate-900',
        'low': 'bg-lime-500 text-slate-900'
    }
    return colors.get(severity, 'bg-slate-500 text-white')

def get_device_type_color(device_type: str) -> str:
    """Retorna cor para tipo de device"""
    colors = {
        'MX': 'bg-violet-500',
        'MS': 'bg-cyan-500',
        'MR': 'bg-green-500',
        'MV': 'bg-orange-500',
        'MG': 'bg-pink-500',
        'MT': 'bg-indigo-500'
    }
    return colors.get(device_type, 'bg-slate-500')

def generate_html(data: dict) -> str:
    """Gera HTML completo do relatório com UX aprimorada"""
    
    org_name = data.get('organization', {}).get('name', 'Unknown')
    org_id = data.get('organization', {}).get('id', 'N/A')
    networks = data.get('networks', [])
    devices = data.get('devices', [])
    issues = data.get('issues', [])
    suggestions = data.get('suggestions', [])
    workflows = data.get('recommended_workflows', [])
    configs = data.get('configurations', {})
    metrics = data.get('metrics', {})
    generated_at = data.get('generated_at', datetime.now().isoformat())
    
    # Contagens
    total_devices = len(devices)
    online_devices = sum(1 for d in devices if d.get('status') == 'online')
    offline_devices = sum(1 for d in devices if d.get('status') == 'offline')
    alerting_devices = sum(1 for d in devices if d.get('status') == 'alerting')
    
    # Contagem por tipo
    device_types = {}
    for d in devices:
        dtype = d.get('type', d.get('model', 'Unknown')[:2])
        device_types[dtype] = device_types.get(dtype, 0) + 1
    
    # Issues por severidade
    critical_issues = sum(1 for i in issues if i.get('severity') == 'critical')
    high_issues = sum(1 for i in issues if i.get('severity') == 'high')
    
    # Health score
    health_score = calculate_health_score(data)
    health_color = 'text-emerald-400' if health_score >= 80 else 'text-amber-400' if health_score >= 60 else 'text-red-400'
    health_bg = 'bg-emerald-500' if health_score >= 80 else 'bg-amber-500' if health_score >= 60 else 'bg-red-500'

    # Dados para Mapa
    map_devices = [
        {
            'name': d.get('name', d.get('serial')),
            'lat': d.get('lat'),
            'lng': d.get('lng'),
            'status': d.get('status', 'unknown'),
            'model': d.get('model', '')
        }
        for d in devices if d.get('lat') and d.get('lng')
    ]
    
    # Configs
    vlans = configs.get('vlans', [])
    ssids = configs.get('ssids', [])
    firewall_l3 = configs.get('firewall', {}).get('l3_rules', [])
    
    html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Meraki Report - {org_name}</title>
    
    <!-- CSS Dependencies -->
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    
    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    fontFamily: {{
                        sans: ['Inter', 'sans-serif'],
                    }},
                    colors: {{
                        meraki: {{
                            green: '#60b561',
                            dark: '#1e293b',
                            card: '#334155'
                        }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{ font-family: 'Inter', sans-serif; }}
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: #0f172a; }}
        ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #475569; }}
        
        .glass-panel {{ 
            background: rgba(30, 41, 59, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(148, 163, 184, 0.1);
        }}
        
        .sidebar-link {{
            transition: all 0.2s ease;
            border-left: 3px solid transparent;
        }}
        .sidebar-link:hover, .sidebar-link.active {{
            background: rgba(255, 255, 255, 0.05);
            border-left-color: #34d399;
            color: #fff;
        }}
        
        /* Map Container */
        #map {{ height: 400px; width: 100%; border-radius: 0.75rem; z-index: 1; }}
        
        /* Animations */
        @keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(10px); }} to {{ opacity: 1; transform: translateY(0); }} }}
        .animate-fade-in {{ animation: fadeIn 0.5s ease-out forwards; }}
    </style>
</head>
<body class="bg-slate-950 text-slate-200 h-screen flex overflow-hidden">

    <!-- Sidebar -->
    <aside class="w-64 bg-slate-900 border-r border-slate-800 flex flex-col z-20">
        <div class="p-6 border-b border-slate-800">
            <div class="flex items-center gap-3">
                <div class="w-10 h-10 bg-gradient-to-br from-emerald-500 to-cyan-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/20">
                    <svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"></path>
                    </svg>
                </div>
                <div>
                    <h1 class="font-bold text-white tracking-tight">Meraki Report</h1>
                    <p class="text-xs text-slate-400">Network Analyst</p>
                </div>
            </div>
        </div>
        
        <nav class="flex-1 overflow-y-auto py-4 space-y-1">
            <a href="#overview" class="sidebar-link active flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
                Overview
            </a>
            <a href="#inventory" class="sidebar-link flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                Inventory
            </a>
            <a href="#security" class="sidebar-link flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>
                Security & Policies
            </a>
            <a href="#wireless" class="sidebar-link flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.111 16.404a5.5 5.5 0 017.778 0M12 20h.01m-7.08-7.071c3.904-3.905 10.236-3.905 14.141 0M1.394 9.393c5.857-5.857 15.355-5.857 21.213 0"></path></svg>
                Wireless
            </a>
             <a href="#topology" class="sidebar-link flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                Topology & Map
            </a>
            <a href="#suggestions" class="sidebar-link flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                Suggestions
            </a>
            <a href="#workflows" class="sidebar-link flex items-center gap-3 px-6 py-3 text-sm font-medium text-slate-300">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
                Workflows
            </a>
        </nav>
        
        <div class="p-6 border-t border-slate-800">
            <div class="bg-slate-800 rounded-lg p-4">
                <p class="text-xs text-slate-400 mb-2">Network Health</p>
                <div class="flex items-end gap-2 mb-2">
                    <span class="text-2xl font-bold text-white">{health_score}%</span>
                    <span class="text-xs {health_color} mb-1">
                        { 'Excellent' if health_score >= 80 else 'Needs Attention' if health_score >= 60 else 'Critical' }
                    </span>
                </div>
                <div class="w-full bg-slate-700 h-1.5 rounded-full overflow-hidden">
                    <div class="{health_bg} h-full rounded-full" style="width: {health_score}%"></div>
                </div>
            </div>
        </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 overflow-y-auto scroll-smooth">
        
        <!-- Top Bar -->
        <header class="sticky top-0 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 z-10 px-8 py-4 flex justify-between items-center">
            <div>
                <h2 class="text-xl font-semibold text-white">{org_name}</h2>
                <p class="text-sm text-slate-400">Organization ID: <span class="font-mono">{org_id}</span></p>
            </div>
            <div class="flex items-center gap-4">
                <div class="text-right">
                    <p class="text-xs text-slate-400">Generated</p>
                    <p class="text-sm font-medium text-slate-200">{generated_at[:16].replace('T', ' ')}</p>
                </div>
            </div>
        </header>

        <div class="p-8 max-w-7xl mx-auto space-y-12 pb-24">
            
            <!-- Overview Section -->
            <section id="overview" class="animate-fade-in">
                <h3 class="text-lg font-medium text-slate-400 mb-6 uppercase tracking-wider">Executive Overview</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <!-- Stat Cards -->
                    <div class="glass-panel rounded-xl p-6 relative overflow-hidden group hover:border-slate-600 transition-colors">
                        <div class="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <svg class="w-24 h-24" fill="currentColor" viewBox="0 0 20 20"><path d="M5.5 16a3.5 3.5 0 01-.369-6.98 4 4 0 117.753-1.977A4.5 4.5 0 1113.5 16h-8z"></path></svg>
                        </div>
                        <p class="text-slate-400 text-sm font-medium">Total Networks</p>
                        <p class="text-3xl font-bold text-white mt-2">{len(networks)}</p>
                    </div>
                    
                    <div class="glass-panel rounded-xl p-6 relative overflow-hidden group hover:border-slate-600 transition-colors">
                        <div class="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <svg class="w-24 h-24" fill="currentColor" viewBox="0 0 20 20"><path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"></path></svg>
                        </div>
                        <p class="text-slate-400 text-sm font-medium">Total Devices</p>
                        <div class="flex items-baseline gap-2 mt-2">
                            <p class="text-3xl font-bold text-white">{total_devices}</p>
                            <span class="text-sm text-emerald-400">{online_devices} Online</span>
                        </div>
                    </div>

                    <div class="glass-panel rounded-xl p-6 relative overflow-hidden group hover:border-slate-600 transition-colors">
                        <div class="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <svg class="w-24 h-24" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path></svg>
                        </div>
                        <p class="text-slate-400 text-sm font-medium">Critical Issues</p>
                        <p class="text-3xl font-bold { 'text-red-400' if critical_issues > 0 else 'text-slate-200' } mt-2">{critical_issues}</p>
                    </div>

                    <div class="glass-panel rounded-xl p-6 relative overflow-hidden group hover:border-slate-600 transition-colors">
                        <div class="absolute right-0 top-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                            <svg class="w-24 h-24" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"></path></svg>
                        </div>
                        <p class="text-slate-400 text-sm font-medium">Actions Required</p>
                        <p class="text-3xl font-bold text-white mt-2">{len(suggestions)}</p>
                    </div>
                </div>

                <!-- Charts Row -->
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
                    <div class="glass-panel rounded-xl p-6 lg:col-span-2">
                        <h4 class="text-sm font-medium text-slate-300 mb-4">Device Distribution</h4>
                        <div class="h-64">
                            <canvas id="deviceChart"></canvas>
                        </div>
                    </div>
                    <div class="glass-panel rounded-xl p-6">
                        <h4 class="text-sm font-medium text-slate-300 mb-4">Status Breakdown</h4>
                        <div class="space-y-4">
                            <div class="flex justify-between items-center">
                                <span class="flex items-center gap-2 text-sm text-slate-400"><span class="w-2 h-2 rounded-full bg-emerald-500"></span> Online</span>
                                <span class="font-bold text-white">{online_devices}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="flex items-center gap-2 text-sm text-slate-400"><span class="w-2 h-2 rounded-full bg-red-500"></span> Offline</span>
                                <span class="font-bold text-white">{offline_devices}</span>
                            </div>
                            <div class="flex justify-between items-center">
                                <span class="flex items-center gap-2 text-sm text-slate-400"><span class="w-2 h-2 rounded-full bg-amber-500"></span> Alerting</span>
                                <span class="font-bold text-white">{alerting_devices}</span>
                            </div>
                        </div>
                        <!-- Pseudo Traffic Chart Placeholders -->
                        <div class="mt-8 pt-8 border-t border-slate-700">
                             <h4 class="text-sm font-medium text-slate-300 mb-4">Top Networks (Clients)</h4>
                             <div class="space-y-3">
                                 <!-- Mock Data for Visual Enrichment -->
                                 <div class="w-full bg-slate-800 rounded-full h-2 mb-1">
                                     <div class="bg-blue-500 h-2 rounded-full" style="width: 75%"></div>
                                 </div>
                                 <div class="flex justify-between text-xs text-slate-500">
                                     <span>Corp Network</span>
                                     <span>124 Clients</span>
                                 </div>
                                 
                                 <div class="w-full bg-slate-800 rounded-full h-2 mb-1">
                                     <div class="bg-blue-500 h-2 rounded-full" style="width: 45%"></div>
                                 </div>
                                 <div class="flex justify-between text-xs text-slate-500">
                                     <span>Guest Network</span>
                                     <span>86 Clients</span>
                                 </div>
                             </div>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Inventory Section -->
            <section id="inventory" class="scroll-mt-24">
                <div class="flex justify-between items-center mb-6">
                    <h3 class="text-lg font-medium text-slate-400 uppercase tracking-wider">Device Inventory</h3>
                    <div class="relative">
                        <input type="text" id="deviceSearch" placeholder="Search devices..." 
                               class="bg-slate-900 border border-slate-700 rounded-lg py-2 px-4 pl-10 text-sm focus:outline-none focus:border-emerald-500 w-64 transition-all">
                        <svg class="w-4 h-4 text-slate-500 absolute left-3 top-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                        </svg>
                    </div>
                </div>
                
                <div class="glass-panel rounded-xl overflow-hidden">
                    <div class="overflow-x-auto">
                        <table class="w-full text-sm text-left">
                            <thead class="bg-slate-900/50 text-slate-400 uppercase text-xs font-semibold">
                                <tr>
                                    <th class="px-6 py-4">Status</th>
                                    <th class="px-6 py-4">Device Name</th>
                                    <th class="px-6 py-4">Model</th>
                                    <th class="px-6 py-4">Serial</th>
                                    <th class="px-6 py-4">IP Address</th>
                                    <th class="px-6 py-4">Firmware</th>
                                </tr>
                            </thead>
                            <tbody class="divide-y divide-slate-800" id="deviceTableBody">
    '''
    
    # JSON dump devices for JS search
    devices_json = json.dumps(devices)
    
    html += f'''
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Pagination Controls -->
                    <div class="bg-slate-900/30 px-6 py-4 border-t border-slate-800 flex items-center justify-between">
                        <span class="text-xs text-slate-400">Showing <span id="startRange">1</span> to <span id="endRange">10</span> of <span id="totalDevices">{len(devices)}</span> devices</span>
                        <div class="flex gap-2">
                            <button id="prevBtn" class="px-3 py-1 text-xs rounded border border-slate-700 hover:bg-slate-800 disabled:opacity-50">Previous</button>
                            <button id="nextBtn" class="px-3 py-1 text-xs rounded border border-slate-700 hover:bg-slate-800 disabled:opacity-50">Next</button>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Security Section -->
            <section id="security" class="scroll-mt-24">
                <h3 class="text-lg font-medium text-slate-400 mb-6 uppercase tracking-wider">Security & Policies</h3>
                
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
                     <div class="glass-panel rounded-xl p-6 col-span-2">
                        <h4 class="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"></path></svg>
                            L3 Firewall Rules
                        </h4>
                        <div class="overflow-x-auto max-h-96">
                            <table class="w-full text-sm text-left">
                                <thead class="bg-slate-900/50 text-slate-400 text-xs uppercase sticky top-0 backdrop-blur-md">
                                    <tr>
                                        <th class="px-4 py-3">Policy</th>
                                        <th class="px-4 py-3">Protocol</th>
                                        <th class="px-4 py-3">Source</th>
                                        <th class="px-4 py-3">Dest</th>
                                        <th class="px-4 py-3">Port</th>
                                        <th class="px-4 py-3">Comment</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-slate-800">
    '''
    
    if firewall_l3:
        for rule in firewall_l3:
            policy_color = 'text-green-400' if rule.get('policy') == 'allow' else 'text-red-400'
            html += f'''
                                    <tr class="hover:bg-slate-800/50">
                                        <td class="px-4 py-3 font-mono font-bold {policy_color} uppercase">{rule.get('policy')}</td>
                                        <td class="px-4 py-3 text-slate-300">{rule.get('protocol')}</td>
                                        <td class="px-4 py-3 font-mono text-slate-400 text-xs">{rule.get('srcCidr')}</td>
                                        <td class="px-4 py-3 font-mono text-slate-400 text-xs">{rule.get('destCidr')}</td>
                                        <td class="px-4 py-3 font-mono text-slate-300">{rule.get('destPort')}</td>
                                        <td class="px-4 py-3 text-slate-500 italic">{rule.get('comment', '-')}</td>
                                    </tr>'''
    else:
        html += '<tr><td colspan="6" class="px-4 py-8 text-center text-slate-500">No firewall rules found or not applicable.</td></tr>'

    html += f'''
                                </tbody>
                            </table>
                        </div>
                     </div>
                     
                     <div class="glass-panel rounded-xl p-6">
                        <h4 class="text-lg font-semibold text-white mb-4">Security Insights</h4>
                        <div class="space-y-4">
                            <div class="bg-slate-900/50 p-4 rounded-lg border border-slate-700">
                                <p class="text-sm text-slate-400">Security Score</p>
                                <div class="flex items-center gap-3 mt-1">
                                    <div class="flex-1 bg-slate-700 h-2 rounded-full overflow-hidden">
                                        <div class="bg-emerald-500 h-full w-3/4"></div>
                                    </div>
                                    <span class="text-emerald-400 font-bold">Good</span>
                                </div>
                            </div>
                            
                            <!-- Issue List Mini -->
                            <div class="space-y-2">
                                <p class="text-xs text-slate-500 uppercase tracking-widest font-semibold">Security Alerts</p>
    '''
    
    security_issues = [i for i in issues if i.get('severity') in ['critical', 'high']]
    if security_issues:
        for issue in security_issues[:3]:
            html += f'''
                                <div class="flex gap-3 items-start p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                                    <svg class="w-5 h-5 text-red-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                                    <div>
                                        <p class="text-sm text-red-200 font-medium">{issue.get('type')}</p>
                                        <p class="text-xs text-red-400/70">{issue.get('message', '')}</p>
                                    </div>
                                </div>
            '''
    else:
        html += '<p class="text-sm text-slate-500 italic">No critical security alerts detected.</p>'
        
    html += '''
                            </div>
                        </div>
                     </div>
                </div>
            </section>
            
            <!-- Topology Map -->
            <section id="topology" class="scroll-mt-24">
                 <h3 class="text-lg font-medium text-slate-400 mb-6 uppercase tracking-wider">Topology & Map</h3>
                 <div class="glass-panel rounded-xl p-1">
                    <div id="map"></div>
                 </div>
            </section>

            <!-- Suggestions -->
            <section id="suggestions" class="scroll-mt-24">
                 <h3 class="text-lg font-medium text-slate-400 mb-6 uppercase tracking-wider">Suggestions</h3>
                 <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    '''
    
    for suggestion in suggestions:
        priority = suggestion.get('priority', 'medium')
        border_color = 'border-red-500/50' if priority == 'high' else 'border-yellow-500/50' if priority == 'medium' else 'border-blue-500/50'
        
        html += f'''
                    <div class="glass-panel rounded-xl p-6 border-l-4 {border_color}">
                        <div class="flex justify-between items-start mb-4">
                            <span class="px-2 py-1 rounded text-xs font-bold uppercase bg-slate-800 text-slate-300">{priority}</span>
                            <svg class="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                        </div>
                        <h4 class="font-bold text-lg mb-2 text-white">{suggestion.get('action')}</h4>
                        <p class="text-sm text-slate-400 mb-4">{suggestion.get('description')}</p>
                        <button class="text-emerald-400 text-sm font-medium hover:text-emerald-300 transition-colors flex items-center gap-1">
                            View details <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 8l4 4m0 0l-4 4m4-4H3"></path></svg>
                        </button>
                    </div>
        '''
        
    html += '''
                 </div>
            </section>
            
            <!-- Workflows -->
            <section id="workflows" class="scroll-mt-24">
                <h3 class="text-lg font-medium text-slate-400 mb-6 uppercase tracking-wider">Recommended Workflows</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
    '''
    
    for wf in workflows:
        html += f'''
                    <div class="glass-panel rounded-xl p-6 relative overflow-hidden">
                        <div class="absolute top-0 right-0 p-6 opacity-5">
                            <svg class="w-32 h-32" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M11.3 1.046A1 1 0 0112 2v5h4a1 1 0 01.82 1.573l-7 10A1 1 0 018 18v-5H4a1 1 0 01-.82-1.573l7-10a1 1 0 011.12-.38z" clip-rule="evenodd"></path></svg>
                        </div>
                        <div class="relative z-10">
                            <h4 class="text-xl font-bold text-white mb-2">{wf.get('name')}</h4>
                            <p class="text-slate-400 mb-6">{wf.get('description', 'Automate this task with Meraki Workflow.')}</p>
                            
                            <div class="bg-slate-900 rounded-lg p-3 font-mono text-xs text-emerald-400 mb-4 border border-slate-700">
                                meraki workflow create -t {wf.get('name').lower().replace(' ', '-')}
                            </div>
                            
                            <button onclick="navigator.clipboard.writeText('meraki workflow create -t {wf.get('name').lower().replace(' ', '-')}')" 
                                    class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                                Copy Command
                            </button>
                        </div>
                    </div>
        '''
        
    html += f'''
                </div>
            </section>

        </div>
    </main>

    <script>
        // Data Injection
        const devices = {devices_json};
        const mapDevices = {json.dumps(map_devices)};
        const deviceTypes = {json.dumps(device_types)};
        
        // --- Navigation Active State ---
        const sections = document.querySelectorAll('section');
        const navLinks = document.querySelectorAll('.sidebar-link');
        
        window.addEventListener('scroll', () => {{
            let current = '';
            const main = document.querySelector('main');
            
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                const sectionHeight = section.clientHeight;
                if (main.scrollTop >= (sectionTop - 150)) {{
                    current = section.getAttribute('id');
                }}
            }});
            
            navLinks.forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href').includes(current)) {{
                    link.classList.add('active');
                }}
            }});
        }}, true); // Capture phase for scrolling div
        
        // --- Device Table Logic ---
        let currentPage = 1;
        const rowsPerPage = 10;
        let filteredDevices = [...devices];
        
        function renderTable() {{
            const tbody = document.getElementById('deviceTableBody');
            tbody.innerHTML = '';
            
            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            const paginatedItems = filteredDevices.slice(start, end);
            
            paginatedItems.forEach(device => {{
                const statusColor = device.status === 'online' ? 'bg-emerald-500' : 
                                  device.status === 'offline' ? 'bg-red-500' : 
                                  device.status === 'alerting' ? 'bg-amber-500' : 'bg-slate-500';
                
                const tr = document.createElement('tr');
                tr.className = 'hover:bg-slate-800/50 transition-colors border-b border-slate-800 last:border-0';
                tr.innerHTML = `
                    <td class="px-6 py-4">
                        <div class="flex items-center gap-2">
                            <span class="w-2.5 h-2.5 rounded-full ${{statusColor}} animate-pulse"></span>
                            <span class="capitalize text-slate-300">${{device.status || 'Unknown'}}</span>
                        </div>
                    </td>
                    <td class="px-6 py-4 font-medium text-white">${{device.name || 'Unnamed'}}</td>
                    <td class="px-6 py-4">
                        <span class="px-2 py-1 rounded bg-slate-800 text-xs font-mono text-slate-300 border border-slate-700">${{device.model}}</span>
                    </td>
                    <td class="px-6 py-4 font-mono text-xs text-slate-400">${{device.serial}}</td>
                    <td class="px-6 py-4 font-mono text-xs text-slate-400">${{device.lan_ip || device.wan_ip || '-'}}</td>
                    <td class="px-6 py-4 text-xs text-slate-500">${{device.firmware || '-'}}</td>
                `;
                tbody.appendChild(tr);
            }});
            
            // Update Controls
            document.getElementById('startRange').textContent = start + 1;
            document.getElementById('endRange').textContent = Math.min(end, filteredDevices.length);
            document.getElementById('totalDevices').textContent = filteredDevices.length;
            
            document.getElementById('prevBtn').disabled = currentPage === 1;
            document.getElementById('nextBtn').disabled = end >= filteredDevices.length;
        }}
        
        document.getElementById('deviceSearch').addEventListener('input', (e) => {{
            const term = e.target.value.toLowerCase();
            filteredDevices = devices.filter(d => 
                (d.name && d.name.toLowerCase().includes(term)) || 
                (d.serial && d.serial.toLowerCase().includes(term)) ||
                (d.model && d.model.toLowerCase().includes(term))
            );
            currentPage = 1;
            renderTable();
        }});
        
        document.getElementById('prevBtn').addEventListener('click', () => {{
            if (currentPage > 1) {{ currentPage--; renderTable(); }}
        }});
        
        document.getElementById('nextBtn').addEventListener('click', () => {{
            if ((currentPage * rowsPerPage) < filteredDevices.length) {{ currentPage++; renderTable(); }}
        }});
        
        renderTable();
        
        // --- Charts ---
        const ctx = document.getElementById('deviceChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: Object.keys(deviceTypes),
                datasets: [{{
                    label: 'Count',
                    data: Object.values(deviceTypes),
                    backgroundColor: '#10b981',
                    borderRadius: 4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        grid: {{ color: '#334155' }},
                        ticks: {{ color: '#94a3b8' }}
                    }},
                    x: {{
                        grid: {{ display: false }},
                        ticks: {{ color: '#94a3b8' }}
                    }}
                }}
            }}
        }});
        
        // --- Map ---
        if (mapDevices.length > 0) {{
            const map = L.map('map').setView([0, 0], 2);
            L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
                subdomains: 'abcd',
                maxZoom: 19
            }}).addTo(map);
            
            const bounds = [];
            mapDevices.forEach(d => {{
                if (d.lat && d.lng) {{
                    const markerColor = d.status === 'online' ? '#10b981' : '#ef4444';
                    const markerHtml = `<div style="background-color: ${{markerColor}}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`;
                    
                    const icon = L.divIcon({{
                        className: 'custom-marker',
                        html: markerHtml,
                        iconSize: [12, 12]
                    }});
                    
                    L.marker([d.lat, d.lng], {{ icon: icon }})
                        .bindPopup(`<b>${{d.name}}</b><br>${{d.model}}<br>${{d.status}}`)
                        .addTo(map);
                    bounds.push([d.lat, d.lng]);
                }}
            }});
            
            if (bounds.length > 0) {{
                map.fitBounds(bounds, {{ padding: [50, 50] }});
            }} else {{
                map.setView([20, 0], 2);
            }}
        }} else {{
            document.getElementById('map').innerHTML = '<div class="h-full flex items-center justify-center text-slate-500">No location data available for devices.</div>';
        }}
        
    </script>
</body>
</html>'''
    
    return html


def serve_report(html_content: str, port: int = DEFAULT_PORT, open_browser: bool = True):
    """Inicia servidor HTTP e abre browser"""
    
    class ReportHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        
        def log_message(self, format, *args):
            pass  # Silencia logs
    
    with socketserver.TCPServer(("", port), ReportHandler) as httpd:
        url = f"http://localhost:{port}"
        print(f"\n{'='*60}")
        print(f"  📊 Meraki Report Dashboard 2.0")
        print(f"{'='*60}")
        print(f"  URL: {url}")
        print(f"  Press Ctrl+C to stop")
        print(f"{'='*60}\n")
        
        if open_browser:
            try:
                webbrowser.get('safari').open(url)
            except:
                webbrowser.open(url)
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n✅ Server stopped.")


def generate_and_serve(json_path: str, port: int = DEFAULT_PORT, open_browser: bool = True, save_html: bool = True):
    """Função principal: carrega JSON, gera HTML, serve e abre browser"""
    
    print(f"📂 Loading: {json_path}")
    data = load_discovery_data(json_path)
    
    print(f"🎨 Generating HTML report 2.0...")
    html = generate_html(data)
    
    # Salva HTML se solicitado
    if save_html:
        json_path = Path(json_path)
        html_path = json_path.parent.parent / 'reports' / f"{json_path.stem}_dashboard.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"💾 Saved: {html_path}")
    
    print(f"🚀 Starting server on port {port}...")
    serve_report(html, port, open_browser)


def main():
    if len(sys.argv) < 2:
        print("Usage: python report_server.py <path_to_discovery_json> [port]")
        print("Example: python report_server.py clients/jose-org/discovery/2026-01-28.json")
        sys.exit(1)
    
    json_path = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_PORT
    
    if not os.path.exists(json_path):
        print(f"❌ Error: File not found: {json_path}")
        sys.exit(1)
    
    generate_and_serve(json_path, port)


if __name__ == "__main__":
    main()
