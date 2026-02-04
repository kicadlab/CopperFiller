import re
import wx

from typing import Dict, List

def _parse_color_string(color_str: str):
    """Парсит строку цвета формата rgb(r,g,b) или rgba(r,g,b,a) в wx.Colour"""
    if not color_str:
        return None
            
    try:
        # Убираем пробелы
        color_str = color_str.strip()
            
        # Парсим rgb(r,g,b)
        if color_str.startswith('rgb('):
            match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
            if match:
                r, g, b = map(int, match.groups())
                return wx.Colour(r, g, b)
            
        # Парсим rgba(r,g,b,a)
        elif color_str.startswith('rgba('):
            match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)', color_str)
            if match:
                r, g, b, a = match.groups()
                r, g, b = map(int, (r, g, b))
                a = float(a)
                # wx.Colour поддерживает alpha только в wxPython 4.1.1+
                # Используем RGB и игнорируем alpha для совместимости
                return wx.Colour(r, g, b)
            
        # Парсим hex формат (если встретится)
        elif color_str.startswith('#'):
            return wx.Colour(color_str)
                
    except Exception as e:
        print(f"Ошибка парсинга цвета {color_str}: {e}")
            
    return None

def create_layer_colors_from_json(json_color: Dict) -> Dict:
    """Создает словарь цветов слоев на основе json_color"""
    layer_colors = {}
        
    # Получаем цвета меди из секции board.copper
    if 'board' in json_color and 'copper' in json_color['board']:
        copper_colors = json_color['board']['copper']
            
        # Основные медные слои
        layer_mapping = {
            'F.Cu': 'f',      # Верхний слой
            'B.Cu': 'b',      # Нижний слой
        }
            
        # Внутренние слои In1.Cu, In2.Cu и т.д.
        for i in range(1, 31):  # Поддерживаем до 30 внутренних слоев
            layer_name = f'In{i}.Cu'
            color_key = f'in{i}'
            layer_mapping[layer_name] = color_key
            
        # Создаем словарь цветов
        for layer_name, color_key in layer_mapping.items():
            if isinstance(copper_colors, dict) and color_key in copper_colors:
                color_str = copper_colors[color_key]
                color = _parse_color_string(color_str)
                if color:
                    layer_colors[layer_name] = color
        
    # Если в json_color есть gerbview.layers, используем их как альтернативу
    if not layer_colors and 'gerbview' in json_color and 'layers' in json_color['gerbview']:
        gerbview_layers = json_color['gerbview']['layers']
        layer_names = ['F.Cu', 'B.Cu'] + [f'In{i}.Cu' for i in range(1, len(gerbview_layers)-1)]
            
        for i, layer_name in enumerate(layer_names):
            if i < len(gerbview_layers):
                color_str = gerbview_layers[i]
                color = _parse_color_string(color_str)
                if color:
                    layer_colors[layer_name] = color
        
    # Добавляем другие слои (не медные) из board секции
    non_copper_mapping = {
        'F.Silks': ('board', 'f_silks'),
        'B.Silks': ('board', 'b_silks'),
        'F.Mask': ('board', 'f_mask'),
        'B.Mask': ('board', 'b_mask'),
        'F.Paste': ('board', 'f_paste'),
        'B.Paste': ('board', 'b_paste'),
        'F.CrtYd': ('board', 'f_crtyd'),
        'B.CrtYd': ('board', 'b_crtyd'),
        'F.Fab': ('board', 'f_fab'),
        'B.Fab': ('board', 'b_fab'),
        'F.Adhes': ('board', 'f_adhes'),
        'B.Adhes': ('board', 'b_adhes'),
        'Edge.Cuts': ('board', 'edge_cuts'),
        'Margin': ('board', 'margin'),
        'Eco1.User': ('board', 'eco1_user'),
        'Eco2.User': ('board', 'eco2_user'),
        'Cmts.User': ('board', 'cmts_user'),
        'Dwgs.User': ('board', 'dwgs_user'),
    }
        
    for layer_name, (section, color_key) in non_copper_mapping.items():
        if section in json_color and color_key in json_color[section]:
            color_str = json_color[section][color_key]
            color = _parse_color_string(color_str)
            if color:
                layer_colors[layer_name] = color
        
    # Добавляем User слои
    for i in range(1, 46):  # KiCad поддерживает до 45 пользовательских слоев
        user_layer = f'User.{i}'
        color_key = f'user_{i}'
            
        # Пробуем сначала из board, потом из schematic/3d_viewer
        for section in ['board', 'schematic', '3d_viewer']:
            if section in json_color and color_key in json_color[section]:
                color_str = json_color[section][color_key]
                color = _parse_color_string(color_str)
                if color:
                    layer_colors[user_layer] = color
                    break
        
    return layer_colors
    
