import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { visualizationAPI } from '../api/client';

interface SpectrogramProps {
  fileId: number;
  episodeId?: string;
  height?: number;
}

const SpectrogramVisualization: React.FC<SpectrogramProps> = ({ fileId, episodeId, height = 400 }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSpectrogram = async () => {
      setLoading(true);
      setError(null);

      try {
        const spectrogramData = await visualizationAPI.getSpectrogram(fileId, episodeId);
        setData(spectrogramData);
      } catch (err: any) {
        setError(err.response?.data?.detail || 'スペクトログラムデータの読み込みに失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchSpectrogram();
  }, [fileId, episodeId]);

  if (loading) {
    return (
      <div style={{
        height: `${height}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f9fafb',
        border: '1px solid #e5e7eb',
        borderRadius: '8px'
      }}>
        <p style={{ color: '#6b7280' }}>スペクトログラムを読み込み中...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        height: `${height}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#fef2f2',
        border: '1px solid #fecaca',
        borderRadius: '8px'
      }}>
        <p style={{ color: '#dc2626' }}>{error}</p>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const plotData = [{
    x: data.times,
    y: data.frequencies,
    z: data.spectrogram,
    type: 'heatmap',
    colorscale: 'Viridis',
    colorbar: {
      title: 'dB',
      titleside: 'right'
    }
  }];

  const layout = {
    title: episodeId ? `スペクトログラム - ${episodeId}` : 'スペクトログラム - ファイル全体',
    xaxis: {
      title: '時間 (秒)',
      showgrid: false
    },
    yaxis: {
      title: '周波数 (Hz)',
      showgrid: false
    },
    height: height,
    margin: {
      l: 60,
      r: 100,
      t: 50,
      b: 50
    },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#ffffff',
    font: {
      family: 'system-ui, -apple-system, sans-serif',
      size: 12
    }
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  };

  return (
    <div style={{ width: '100%' }}>
      <Plot
        data={plotData as any}
        layout={layout as any}
        config={config}
        style={{ width: '100%' }}
        useResizeHandler={true}
      />
    </div>
  );
};

export default SpectrogramVisualization;
