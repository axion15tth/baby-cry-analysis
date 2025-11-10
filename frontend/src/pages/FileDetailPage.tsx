import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { filesAPI as audioAPI, analysisAPI } from '../api/client';
import type { AudioFile, AnalysisResult, CryEpisode } from '../types/index';
import Plotly from 'plotly.js-dist-min';
import createPlotlyComponent from 'react-plotly.js/factory';
import WaveformVisualization from '../components/WaveformVisualization';
import SpectrogramVisualization from '../components/SpectrogramVisualization';
const Plot = createPlotlyComponent(Plotly);

const FileDetailPage: React.FC = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [audioFile, setAudioFile] = useState<AudioFile | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [analysisProgress, setAnalysisProgress] = useState('');
  const [analysisProgressPercent, setAnalysisProgressPercent] = useState(0);

  useEffect(() => {
    if (fileId) {
      loadFileData(parseInt(fileId));
    }
  }, [fileId]);

  const loadFileData = async (id: number) => {
    try {
      setLoading(true);
      const file = await audioAPI.get(id);
      setAudioFile(file);

      // 解析結果が存在する場合は取得
      if (file.status === 'completed') {
        try {
          const results = await analysisAPI.results(id);
          if (results.length > 0) {
            setAnalysisResult(results[0]);
          }
        } catch (err) {
          console.log('解析結果がまだありません');
        }
      } else if (file.status === 'processing') {
        // 処理中の場合、ステータスを監視
        const checkStatus = setInterval(async () => {
          const status = await analysisAPI.status(id);

          if (status.progress !== undefined && status.progress !== null) {
            setAnalysisProgressPercent(status.progress);
            setAnalysisProgress(`${status.message || '解析中...'} (${status.progress}%)`);
          } else {
            setAnalysisProgress(status.message);
          }

          if (status.status === 'completed') {
            clearInterval(checkStatus);
            setAnalysisProgress('');
            setAnalysisProgressPercent(0);
            loadFileData(id);
          } else if (status.status === 'failed') {
            clearInterval(checkStatus);
            setAnalysisProgress('解析に失敗しました');
            setAnalysisProgressPercent(0);
          }
        }, 2000);

        return () => clearInterval(checkStatus);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'ファイルの読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleStartAnalysis = async () => {
    if (!audioFile) return;

    try {
      setLoading(true);
      setError('');
      setAnalysisProgress('解析を開始しています...');
      await analysisAPI.start(audioFile.id);

      setAudioFile({ ...audioFile, status: 'processing' });

      // ステータス監視を開始
      const checkStatus = setInterval(async () => {
        const status = await analysisAPI.status(audioFile.id);

        if (status.progress !== undefined && status.progress !== null) {
          setAnalysisProgressPercent(status.progress);
          setAnalysisProgress(`${status.message || '解析中...'} (${status.progress}%)`);
        } else {
          setAnalysisProgress(status.message);
        }

        if (status.status === 'completed') {
          clearInterval(checkStatus);
          setAnalysisProgress('');
          setAnalysisProgressPercent(0);
          loadFileData(audioFile.id);
        } else if (status.status === 'failed') {
          clearInterval(checkStatus);
          setAnalysisProgress('解析に失敗しました');
          setAnalysisProgressPercent(0);
        }
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || '解析の開始に失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const renderCryEpisodesPlot = () => {
    if (!analysisResult || !analysisResult.result_data.cry_episodes) {
      return null;
    }

    const episodes = analysisResult.result_data.cry_episodes;

    // 各エピソードを個別の行に表示（Ganttチャートスタイル）
    const data = episodes.map((ep: CryEpisode, idx: number) => ({
      type: 'bar' as const,
      orientation: 'h' as const,
      x: [ep.duration],
      y: [`エピソード ${idx + 1}`],
      base: [ep.start_time],
      marker: {
        color: `hsl(${(idx * 137.5) % 360}, 70%, 60%)`, // 色相を変えて各エピソードを区別
        line: {
          color: '#1e293b',
          width: 1
        }
      },
      text: [`${ep.start_time.toFixed(2)}s - ${ep.end_time.toFixed(2)}s<br>継続: ${ep.duration.toFixed(2)}s<br>信頼度: ${(ep.confidence * 100).toFixed(1)}%`],
      hovertemplate: '<b>%{y}</b><br>%{text}<extra></extra>',
      showlegend: false
    }));

    // グラフの高さを動的に調整（エピソード数に応じて）
    const graphHeight = Math.max(250, episodes.length * 40 + 100);

    return (
      <Plot
        data={data}
        layout={{
          title: {
            text: '泣き声エピソード検出タイムライン',
            font: { size: 16, color: '#1e293b' }
          },
          xaxis: {
            title: '時間 (秒)',
            color: '#1e293b',
            gridcolor: '#e5e7eb',
            zeroline: false
          },
          yaxis: {
            color: '#1e293b',
            autorange: 'reversed', // エピソード1を上に表示
            gridcolor: '#e5e7eb'
          },
          height: graphHeight,
          plot_bgcolor: 'white',
          paper_bgcolor: 'white',
          font: { color: '#1e293b' },
          margin: { l: 120, r: 40, t: 60, b: 60 },
          bargap: 0.3
        }}
        config={{ responsive: true }}
        style={{ width: '100%' }}
      />
    );
  };

  const renderAcousticFeaturesPlot = () => {
    if (!analysisResult || !analysisResult.result_data.acoustic_features) {
      return null;
    }

    const features = analysisResult.result_data.acoustic_features;
    const episodeKeys = Object.keys(features);

    if (episodeKeys.length === 0) {
      return null;
    }

    return episodeKeys.map((key) => {
      const episodeFeatures = features[key];

      if (!episodeFeatures || episodeFeatures.length === 0) {
        return null;
      }

      const times = episodeFeatures.map(f => f.time);
      const f0Values = episodeFeatures.map(f => f.f0);
      const f1Values = episodeFeatures.map(f => f.f1);
      const f2Values = episodeFeatures.map(f => f.f2);
      const f3Values = episodeFeatures.map(f => f.f3);

      // エピソード番号を1から始めるように調整
      const episodeNumber = parseInt(key.replace('episode_', '')) + 1;

      return (
        <div key={key} style={{ marginBottom: '30px' }}>
          <h4>エピソード {episodeNumber}</h4>
          <Plot
            data={[
              {
                x: times,
                y: f0Values,
                mode: 'lines',
                name: 'F0 (基本周波数)',
                line: { color: 'blue' }
              },
              {
                x: times,
                y: f1Values,
                mode: 'lines',
                name: 'F1',
                line: { color: 'red' }
              },
              {
                x: times,
                y: f2Values,
                mode: 'lines',
                name: 'F2',
                line: { color: 'green' }
              },
              {
                x: times,
                y: f3Values,
                mode: 'lines',
                name: 'F3',
                line: { color: 'orange' }
              }
            ]}
            layout={{
              title: { text: '音響特徴（F0とフォルマント）', font: { size: 16, color: '#1e293b' } },
              xaxis: { title: '時間 (秒)', color: '#1e293b' },
              yaxis: { title: '周波数 (Hz)', color: '#1e293b' },
              height: 400,
              plot_bgcolor: 'white',
              paper_bgcolor: 'white',
              font: { color: '#1e293b' }
            }}
            config={{ responsive: true }}
            style={{ width: '100%' }}
          />
        </div>
      );
    });
  };

  const renderStatistics = () => {
    if (!analysisResult || !analysisResult.result_data.statistics) {
      return null;
    }

    const stats = analysisResult.result_data.statistics;
    const episodeKeys = Object.keys(stats);

    if (episodeKeys.length === 0) {
      return null;
    }

    // パラメータ名の日本語マッピング
    const paramNameMap: Record<string, string> = {
      'f0': 'F0 (基本周波数)',
      'f1': 'F1 (第1フォルマント)',
      'f2': 'F2 (第2フォルマント)',
      'f3': 'F3 (第3フォルマント)',
      'intensity': '音響強度',
      'hnr': 'HNR (調和雑音比)',
      'jitter': 'ジッター',
      'shimmer': 'シマー'
    };

    return episodeKeys.map((key) => {
      const episodeStats = stats[key];
      // エピソード番号を1から始めるように調整
      const episodeNumber = parseInt(key.replace('episode_', '')) + 1;

      // 統計パラメータと単一値パラメータを分離
      const statisticsParams: [string, any][] = [];
      const singleValueParams: [string, any][] = [];

      Object.entries(episodeStats).forEach(([param, values]) => {
        if (typeof values === 'object' && values !== null && 'mean' in values) {
          statisticsParams.push([param, values]);
        } else if (typeof values === 'number') {
          singleValueParams.push([param, values]);
        }
      });

      return (
        <div key={key} style={{
          marginBottom: '30px',
          backgroundColor: 'white',
          padding: '24px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h4 style={{
            marginTop: 0,
            marginBottom: '20px',
            color: '#1e293b',
            fontSize: '18px',
            borderBottom: '2px solid #3b82f6',
            paddingBottom: '8px'
          }}>
            エピソード {episodeNumber} の統計
          </h4>

          {/* 音響パラメータの統計（テーブル形式） */}
          {statisticsParams.length > 0 && (
            <div style={{ overflowX: 'auto', marginBottom: '20px' }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse',
                fontSize: '14px'
              }}>
                <thead>
                  <tr style={{ backgroundColor: '#f8fafc' }}>
                    <th style={{
                      padding: '12px',
                      textAlign: 'left',
                      borderBottom: '2px solid #e2e8f0',
                      color: '#475569',
                      fontWeight: '600'
                    }}>パラメータ</th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      borderBottom: '2px solid #e2e8f0',
                      color: '#475569',
                      fontWeight: '600'
                    }}>平均</th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      borderBottom: '2px solid #e2e8f0',
                      color: '#475569',
                      fontWeight: '600'
                    }}>標準偏差</th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      borderBottom: '2px solid #e2e8f0',
                      color: '#475569',
                      fontWeight: '600'
                    }}>最小値</th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      borderBottom: '2px solid #e2e8f0',
                      color: '#475569',
                      fontWeight: '600'
                    }}>中央値</th>
                    <th style={{
                      padding: '12px',
                      textAlign: 'right',
                      borderBottom: '2px solid #e2e8f0',
                      color: '#475569',
                      fontWeight: '600'
                    }}>最大値</th>
                  </tr>
                </thead>
                <tbody>
                  {statisticsParams.map(([param, values]) => (
                    <tr key={param} style={{ borderBottom: '1px solid #f1f5f9' }}>
                      <td style={{
                        padding: '12px',
                        fontWeight: '500',
                        color: '#1e293b'
                      }}>
                        {paramNameMap[param] || param.toUpperCase()}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#334155' }}>
                        {values.mean?.toFixed(2) ?? '-'}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#334155' }}>
                        {values.std?.toFixed(2) ?? '-'}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#334155' }}>
                        {values.min?.toFixed(2) ?? '-'}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#334155' }}>
                        {values.median?.toFixed(2) ?? '-'}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', color: '#334155' }}>
                        {values.max?.toFixed(2) ?? '-'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* その他のパラメータ（カード形式） */}
          {singleValueParams.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
              {singleValueParams.map(([param, value]) => (
                <div key={param} style={{
                  backgroundColor: '#f8fafc',
                  padding: '16px',
                  borderRadius: '6px',
                  border: '1px solid #e2e8f0'
                }}>
                  <div style={{
                    fontSize: '13px',
                    color: '#64748b',
                    marginBottom: '4px',
                    fontWeight: '500'
                  }}>
                    {paramNameMap[param] || param}
                  </div>
                  <div style={{
                    fontSize: '24px',
                    fontWeight: '600',
                    color: '#1e293b'
                  }}>
                    {value.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    });
  };

  if (loading && !audioFile) {
    return <div style={{ textAlign: 'center', padding: '50px' }}>読み込み中...</div>;
  }

  if (error && !audioFile) {
    return (
      <div style={{ textAlign: 'center', padding: '50px', color: 'red' }}>
        エラー: {error}
        <div style={{ marginTop: '20px' }}>
          <button onClick={() => navigate('/')}>ダッシュボードに戻る</button>
        </div>
      </div>
    );
  }

  if (!audioFile) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        ファイルが見つかりません
        <div style={{ marginTop: '20px' }}>
          <button onClick={() => navigate('/')}>ダッシュボードに戻る</button>
        </div>
      </div>
    );
  }

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f5f7fa'
    }}>
      {/* ヘッダー */}
      <div style={{
        backgroundColor: '#1e293b',
        color: 'white',
        padding: '16px 0',
        borderBottom: '1px solid #334155'
      }}>
        <div style={{
          margin: '0 auto',
          padding: '0 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          width: '100%',
          boxSizing: 'border-box'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <h1 style={{
              fontSize: '18px',
              fontWeight: '600',
              margin: 0,
              letterSpacing: '-0.3px'
            }}>Baby Cry Analysis</h1>
            <button
              onClick={() => navigate('/')}
              style={{
                padding: '6px 12px',
                backgroundColor: 'transparent',
                color: 'white',
                border: '1px solid #475569',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '500'
              }}
            >
              ← ダッシュボード
            </button>
          </div>
          <button
            onClick={handleLogout}
            style={{
              padding: '8px 16px',
              backgroundColor: 'transparent',
              color: 'white',
              border: '1px solid #475569',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '13px',
              fontWeight: '500'
            }}
          >
            ログアウト
          </button>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>

      <h2 style={{ color: '#1e293b', marginBottom: '24px' }}>ファイル詳細</h2>

      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '8px',
        marginBottom: '24px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ marginTop: 0 }}>ファイル情報</h3>
        <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr', gap: '10px' }}>
          <div><strong>ファイル名:</strong></div>
          <div>{audioFile.original_filename}</div>

          <div><strong>アップロード日時:</strong></div>
          <div>{new Date(audioFile.uploaded_at).toLocaleString('ja-JP')}</div>

          <div><strong>ファイルサイズ:</strong></div>
          <div>{(audioFile.file_size / 1024).toFixed(2)} KB</div>

          <div><strong>サンプルレート:</strong></div>
          <div>{audioFile.sample_rate ? `${audioFile.sample_rate} Hz` : 'N/A'}</div>

          <div><strong>継続時間:</strong></div>
          <div>{audioFile.duration ? `${audioFile.duration.toFixed(2)} 秒` : 'N/A'}</div>

          <div><strong>ステータス:</strong></div>
          <div>
            <span style={{
              padding: '4px 12px',
              borderRadius: '12px',
              fontSize: '14px',
              backgroundColor:
                audioFile.status === 'completed' ? '#d4edda' :
                audioFile.status === 'processing' ? '#fff3cd' :
                audioFile.status === 'failed' ? '#f8d7da' : '#d1ecf1',
              color:
                audioFile.status === 'completed' ? '#155724' :
                audioFile.status === 'processing' ? '#856404' :
                audioFile.status === 'failed' ? '#721c24' : '#0c5460'
            }}>
              {
                audioFile.status === 'uploaded' ? 'アップロード済み' :
                audioFile.status === 'processing' ? '処理中' :
                audioFile.status === 'completed' ? '完了' :
                audioFile.status === 'failed' ? '失敗' : audioFile.status
              }
            </span>
          </div>
        </div>

        <div style={{ marginTop: '20px' }}>
          <button
            onClick={() => {
              const url = `http://localhost:8000/api/v1/audio-files/${audioFile.id}/stream`;
              const link = document.createElement('a');
              link.href = url;
              link.download = audioFile.original_filename;
              link.click();
            }}
            style={{
              padding: '10px 20px',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500'
            }}
          >
            ファイルをダウンロード
          </button>
        </div>

        {audioFile.status === 'uploaded' && (
          <div style={{ marginTop: '20px' }}>
            <button
              onClick={handleStartAnalysis}
              disabled={loading}
              style={{
                padding: '10px 20px',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1,
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              解析を開始
            </button>
          </div>
        )}

        {audioFile.status === 'processing' && (
          <div style={{ marginTop: '20px' }}>
            <div style={{ marginBottom: '10px' }}>{analysisProgress}</div>
            <div style={{
              width: '100%',
              height: '20px',
              backgroundColor: '#e5e7eb',
              borderRadius: '10px',
              overflow: 'hidden'
            }}>
              <div style={{
                width: `${analysisProgressPercent}%`,
                height: '100%',
                backgroundColor: '#3b82f6',
                transition: 'width 0.3s ease',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {analysisProgressPercent > 10 && `${analysisProgressPercent}%`}
              </div>
            </div>
          </div>
        )}

        {error && (
          <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f8d7da', color: '#721c24', borderRadius: '4px' }}>
            {error}
          </div>
        )}
      </div>

      {/* 波形とスペクトログラム */}
      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '24px'
      }}>
        <h4 style={{
          fontSize: '16px',
          fontWeight: '500',
          color: '#374151',
          marginBottom: '12px',
          margin: '0 0 12px 0'
        }}>波形</h4>
        <WaveformVisualization
          fileId={audioFile.id}
          height={300}
        />
      </div>

      <div style={{
        backgroundColor: 'white',
        padding: '24px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        marginBottom: '24px'
      }}>
        <h4 style={{
          fontSize: '16px',
          fontWeight: '500',
          color: '#374151',
          marginBottom: '12px',
          margin: '0 0 12px 0'
        }}>スペクトログラム</h4>
        <SpectrogramVisualization
          fileId={audioFile.id}
          height={400}
        />
      </div>

      {audioFile.status === 'completed' && analysisResult && (
        <div>
          <h3 style={{ color: '#1e293b', marginBottom: '24px' }}>解析結果</h3>

          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            marginBottom: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ marginTop: 0, color: '#1e293b' }}>泣き声エピソード</h4>
            <div style={{ marginBottom: '16px', color: '#1e293b' }}>
              検出されたエピソード数: {analysisResult.result_data.cry_episodes.length}
            </div>
            {renderCryEpisodesPlot()}
          </div>

          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            marginBottom: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ marginTop: 0, color: '#1e293b' }}>音響特徴</h4>
            {renderAcousticFeaturesPlot()}
          </div>

          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '8px',
            marginBottom: '24px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
          }}>
            <h4 style={{ marginTop: 0, color: '#1e293b' }}>統計情報</h4>
            {renderStatistics()}
          </div>
        </div>
      )}

      {audioFile.status === 'failed' && (
        <div style={{
          padding: '20px',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderRadius: '8px',
          marginTop: '20px'
        }}>
          解析に失敗しました。もう一度お試しください。
        </div>
      )}
      </div>
    </div>
  );
};

export default FileDetailPage;
