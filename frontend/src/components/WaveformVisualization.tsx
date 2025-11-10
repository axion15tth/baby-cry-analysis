import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { visualizationAPI } from '../api/client';

interface WaveformProps {
  fileId: number;
  episodeId?: string;
  height?: number;
}

const WaveformVisualization: React.FC<WaveformProps> = ({ fileId, episodeId, height = 300 }) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchWaveform = async () => {
      setLoading(true);
      setError(null);

      try {
        const waveformData = await visualizationAPI.getWaveform(fileId, episodeId);
        setData(waveformData);
      } catch (err: any) {
        setError(err.response?.data?.detail || '波形データの読み込みに失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchWaveform();
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
        <p style={{ color: '#6b7280' }}>波形を読み込み中...</p>
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
    x: data.time,
    y: data.amplitude,
    type: 'scatter',
    mode: 'lines',
    name: '振幅',
    line: {
      color: '#3b82f6',
      width: 1
    }
  }];

  const layout = {
    title: episodeId ? `波形 - ${episodeId}` : '波形 - ファイル全体',
    xaxis: {
      title: '時間 (秒)',
      showgrid: true,
      gridcolor: '#e5e7eb'
    },
    yaxis: {
      title: '振幅',
      showgrid: true,
      gridcolor: '#e5e7eb'
    },
    height: height,
    margin: {
      l: 60,
      r: 30,
      t: 50,
      b: 50
    },
    paper_bgcolor: '#ffffff',
    plot_bgcolor: '#f9fafb',
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

export default WaveformVisualization;
