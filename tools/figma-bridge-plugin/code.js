// Antigravity Figma Live Bridge - Canvas Automation Controller

figma.showUI(__html__, { width: 320, height: 260 });

function hexToRgb(hex) {
  const clean = hex.replace('#', '');
  const bigint = parseInt(clean, 16);
  if (clean.length === 6) {
    const r = (bigint >> 16) & 255;
    const g = (bigint >> 8) & 255;
    const b = bigint & 255;
    return { r: r / 255, g: g / 255, b: b / 255 };
  }
  return { r: 1, g: 1, b: 1 };
}

figma.ui.onmessage = async (msg) => {
  if (!msg || !msg.action) return;

  try {
    if (msg.action === 'create_svg_node') {
      // SVG文字列から直接キャンバスにFrame/ベクターノードを作成
      const svgString = msg.svg;
      if (!svgString) {
        figma.ui.postMessage({ type: 'log', text: '❌ SVGデータが空です' });
        return;
      }

      const node = figma.createNodeFromSvg(svgString);
      node.name = msg.name || 'MightyLink_Live_Wireframe';
      
      // 現在のビューポートの中央に配置
      const center = figma.viewport.center;
      node.x = center.x - node.width / 2;
      node.y = center.y - node.height / 2;

      figma.currentPage.appendChild(node);
      figma.currentPage.selection = [node];
      figma.viewport.scrollAndZoomIntoView([node]);

      figma.ui.postMessage({ type: 'log', text: `✨ ノード作成成功: ${node.name}` });
      figma.notify('🚀 Antigravity からワイヤーフレームを直接作成しました！', { timeout: 3000 });
    }

    else if (msg.action === 'update_selection_color') {
      // 選択中または指定ノードの色を変更
      const color = hexToRgb(msg.hex || '#baff66');
      const selection = figma.currentPage.selection;
      
      if (selection.length === 0) {
        figma.ui.postMessage({ type: 'log', text: '⚠️ レイヤーが選択されていません' });
        return;
      }

      for (const node of selection) {
        if ('fills' in node) {
          node.fills = [{ type: 'SOLID', color: color }];
        }
      }
      figma.ui.postMessage({ type: 'log', text: `🎨 選択レイヤーの色を変更しました: ${msg.hex}` });
      figma.notify(`🎨 カラーを ${msg.hex} に変更しました`);
    }

    else if (msg.action === 'notify') {
      figma.notify(msg.message || 'Antigravity Notification');
    }
  } catch (err) {
    figma.ui.postMessage({ type: 'log', text: `❌ エラー: ${err.message}` });
  }
};
