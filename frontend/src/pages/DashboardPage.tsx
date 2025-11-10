import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { filesAPI, analysisAPI, exportAPI } from '../api/client';
import type { AudioFile, AnalysisResult } from '../types/index';
import WaveformVisualization from '../components/WaveformVisualization';
import SpectrogramVisualization from '../components/SpectrogramVisualization';
import AudioPlayer from '../components/AudioPlayer';

interface Notification {
  message: string;
  type: 'success' | 'error' | 'info';
}

const DashboardPage: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [files, setFiles] = useState<AudioFile[]>([]);
  const [selectedFile, setSelectedFile] = useState<AudioFile | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [analyzingFileId, setAnalyzingFileId] = useState<number | null>(null);
  const [analysisProgress, setAnalysisProgress] = useState('');
  const [analysisProgressPercent, setAnalysisProgressPercent] = useState(0);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<Notification | null>(null);
  const [autoAnalyze, setAutoAnalyze] = useState(false);
  const [recordingStartTime, setRecordingStartTime] = useState('');
  const [isDragging, setIsDragging] = useState(false);

  // エピソード数を格納する状態（fileId -> episodeCount）
  const [episodeCounts, setEpisodeCounts] = useState<Record<number, number>>({});

  // 検索・フィルター用の状態
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'date' | 'name'>('date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // ページネーション用の状態
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const showNotification = (message: string, type: 'success' | 'error' | 'info') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 5000);
  };

  const loadFiles = async () => {
    setLoading(true);
    try {
      const data = await filesAPI.list();
      setFiles(data.files);
      // 完了したファイルのエピソード数を取得
      await loadEpisodeCounts(data.files);
    } catch (error) {
      console.error('Failed to load files:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadEpisodeCounts = async (fileList: AudioFile[]) => {
    const completedFiles = fileList.filter(f => f.status === 'completed');
    const counts: Record<number, number> = {};

    for (const file of completedFiles) {
      try {
        const results = await analysisAPI.results(file.id);
        if (results.length > 0) {
          counts[file.id] = results[0].result_data.cry_episodes.length;
        }
      } catch (error) {
        console.error(`Failed to load episode count for file ${file.id}:`, error);
      }
    }

    setEpisodeCounts(counts);
  };

  useEffect(() => {
    loadFiles();
  }, []);

  // フィルターとソートを適用したファイルリストを計算
  const filteredAndSortedFiles = React.useMemo(() => {
    let result = [...files];

    // 検索フィルター（ファイル名）
    if (searchQuery) {
      result = result.filter(file =>
        file.filename.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // ステータスフィルター
    if (statusFilter !== 'all') {
      result = result.filter(file => file.status === statusFilter);
    }

    // ソート
    result.sort((a, b) => {
      if (sortBy === 'date') {
        const dateA = new Date(a.uploaded_at).getTime();
        const dateB = new Date(b.uploaded_at).getTime();
        return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
      } else {
        const nameA = a.filename.toLowerCase();
        const nameB = b.filename.toLowerCase();
        if (sortOrder === 'desc') {
          return nameB.localeCompare(nameA);
        } else {
          return nameA.localeCompare(nameB);
        }
      }
    });

    return result;
  }, [files, searchQuery, statusFilter, sortBy, sortOrder]);

  // ページネーション計算
  const totalPages = Math.ceil(filteredAndSortedFiles.length / itemsPerPage);
  const paginatedFiles = React.useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return filteredAndSortedFiles.slice(startIndex, endIndex);
  }, [filteredAndSortedFiles, currentPage, itemsPerPage]);

  // フィルターが変更されたら1ページ目に戻る
  React.useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, statusFilter, sortBy, sortOrder]);

  // ファイルアップロードの共通ロジック
  const uploadFile = async (file: File) => {
    setUploading(true);
    setUploadProgress(0);

    try {
      // プログレスバーのシミュレーション
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) return prev;
          return prev + 10;
        });
      }, 200);

      // 録音開始時刻をISO 8601形式に変換
      const recordingStartTimeISO = recordingStartTime ? new Date(recordingStartTime).toISOString() : undefined;

      await filesAPI.upload(file, recordingStartTimeISO);

      clearInterval(progressInterval);
      setUploadProgress(100);

      const data = await filesAPI.list();
      setFiles(data.files);
      showNotification('ファイルがアップロードされました', 'success');

      // 自動解析が有効な場合、最新のファイルを解析
      if (autoAnalyze && data.files.length > 0) {
        // 最新のファイルを取得（uploaded ステータスのもの）
        const latestFile = data.files
          .filter(f => f.status === 'uploaded')
          .sort((a, b) => new Date(b.uploaded_at).getTime() - new Date(a.uploaded_at).getTime())[0];

        if (latestFile) {
          setTimeout(() => {
            handleAnalyze(latestFile.id);
          }, 1500);
        }
      }

      // リセット
      setTimeout(() => {
        setUploadProgress(0);
      }, 1000);
    } catch (error: any) {
      showNotification('アップロードに失敗しました: ' + (error.response?.data?.detail || error.message), 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    await uploadFile(file);
    e.target.value = '';
  };

  // ドラッグ&ドロップイベントハンドラ
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (!file) {
      showNotification('ファイルが見つかりません', 'error');
      return;
    }

    // ファイルタイプの検証（音声ファイルのみ）
    const validTypes = ['audio/wav', 'audio/wave', 'audio/x-wav', 'audio/mpeg', 'audio/mp3'];
    if (!validTypes.includes(file.type) && !file.name.endsWith('.wav') && !file.name.endsWith('.mp3')) {
      showNotification('音声ファイル（WAV, MP3）のみアップロード可能です', 'error');
      return;
    }

    await uploadFile(file);
  };

  const handleAnalyze = async (fileId: number) => {
    setAnalyzingFileId(fileId);
    setAnalysisProgress('解析を開始しています...');
    setAnalysisProgressPercent(0);

    try {
      await analysisAPI.start(fileId);
      showNotification('解析を開始しました', 'info');

      const checkStatus = setInterval(async () => {
        try {
          const status = await analysisAPI.status(fileId);

          // 進捗率を更新
          if (status.progress !== undefined && status.progress !== null) {
            setAnalysisProgressPercent(status.progress);
            setAnalysisProgress(`${status.message || '解析中...'} (${status.progress}%)`);
          } else {
            setAnalysisProgress(status.message || '解析中...');
          }

          if (status.status === 'completed') {
            clearInterval(checkStatus);
            await loadFiles();
            showNotification('解析が完了しました', 'success');
            setAnalyzingFileId(null);
            setAnalysisProgress('');
            setAnalysisProgressPercent(0);
          } else if (status.status === 'failed') {
            clearInterval(checkStatus);
            showNotification('解析に失敗しました', 'error');
            setAnalyzingFileId(null);
            setAnalysisProgress('');
            setAnalysisProgressPercent(0);
          }
        } catch (error) {
          console.error('Status check error:', error);
        }
      }, 2000); // 2秒ごとにチェック
    } catch (error: any) {
      showNotification('解析開始に失敗しました: ' + (error.response?.data?.detail || error.message), 'error');
      setAnalyzingFileId(null);
      setAnalysisProgress('');
      setAnalysisProgressPercent(0);
    }
  };

  const handleViewResults = async (fileId: number) => {
    try {
      const results = await analysisAPI.results(fileId);
      if (results.length > 0) {
        setAnalysisResult(results[0]);
        const file = files.find((f) => f.id === fileId);
        setSelectedFile(file || null);
      }
    } catch (error: any) {
      showNotification('結果の取得に失敗しました: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

  const handleExport = (fileId: number, format: 'csv' | 'excel' | 'pdf') => {
    const token = localStorage.getItem('token');
    let url = '';

    switch (format) {
      case 'csv':
        url = exportAPI.episodesCSV(fileId);
        break;
      case 'excel':
        url = exportAPI.excel(fileId);
        break;
      case 'pdf':
        url = exportAPI.pdf(fileId);
        break;
    }

    fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    })
    .then(response => response.blob())
    .then(blob => {
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `analysis_${fileId}.${format === 'csv' ? 'csv' : format === 'excel' ? 'xlsx' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(blobUrl);
      showNotification(`${format.toUpperCase()}ファイルをダウンロードしました`, 'success');
    })
    .catch(error => {
      showNotification('エクスポートに失敗しました: ' + error.message, 'error');
    });
  };

  const handleDelete = async (fileId: number, filename: string) => {
    if (!window.confirm(`「${filename}」を削除しますか？この操作は取り消せません。`)) {
      return;
    }

    try {
      await filesAPI.delete(fileId);
      await loadFiles();
      showNotification('ファイルを削除しました', 'success');

      // 削除したファイルが選択されていた場合はクリア
      if (selectedFile?.id === fileId) {
        setSelectedFile(null);
        setAnalysisResult(null);
      }
    } catch (error: any) {
      showNotification('削除に失敗しました: ' + (error.response?.data?.detail || error.message), 'error');
    }
  };

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
          <h1 style={{
            fontSize: '18px',
            fontWeight: '600',
            margin: 0,
            letterSpacing: '-0.3px'
          }}>Baby Cry Analysis</h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <span style={{ fontSize: '13px', color: '#cbd5e1' }}>{user?.email}</span>
            <button
              onClick={logout}
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
      </div>

      {/* 通知バナー */}
      {notification && (
        <div style={{
          backgroundColor:
            notification.type === 'success' ? '#d1fae5' :
            notification.type === 'error' ? '#fee2e2' : '#dbeafe',
          color:
            notification.type === 'success' ? '#065f46' :
            notification.type === 'error' ? '#991b1b' : '#1e40af',
          padding: '12px 32px',
          fontSize: '14px',
          fontWeight: '500',
          borderBottom: '1px solid' + (
            notification.type === 'success' ? '#a7f3d0' :
            notification.type === 'error' ? '#fecaca' : '#bfdbfe'
          ),
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            style={{
              background: 'none',
              border: 'none',
              color: 'inherit',
              cursor: 'pointer',
              fontSize: '18px',
              padding: '0 8px',
              fontWeight: 'bold'
            }}
          >
            ×
          </button>
        </div>
      )}

      <div style={{ padding: '32px', boxSizing: 'border-box' }}>
        {/* ファイルアップロード */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <h2 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: '#1a1a1a',
            marginBottom: '16px',
            margin: '0 0 16px 0'
          }}>音声ファイルアップロード</h2>
          <div>
            <div style={{ marginBottom: '12px' }}>
              <label
                htmlFor="recordingStartTime"
                style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '6px'
                }}
              >
                録音開始時刻（オプション）
              </label>
              <input
                type="datetime-local"
                id="recordingStartTime"
                value={recordingStartTime}
                onChange={(e) => setRecordingStartTime(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
              />
              <p style={{
                fontSize: '12px',
                color: '#6b7280',
                margin: '4px 0 0 0'
              }}>
                録音を開始した日時を入力すると、解析結果に絶対時刻が表示されます
              </p>
            </div>
            <div style={{
              marginBottom: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <input
                type="checkbox"
                id="autoAnalyze"
                checked={autoAnalyze}
                onChange={(e) => setAutoAnalyze(e.target.checked)}
                style={{
                  width: '16px',
                  height: '16px',
                  cursor: 'pointer'
                }}
              />
              <label
                htmlFor="autoAnalyze"
                style={{
                  fontSize: '14px',
                  color: '#374151',
                  cursor: 'pointer',
                  userSelect: 'none'
                }}
              >
                アップロード後に自動的に解析を開始
              </label>
            </div>
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              style={{
                position: 'relative',
                border: isDragging ? '2px dashed #3b82f6' : '2px dashed #d1d5db',
                borderRadius: '8px',
                padding: '24px',
                textAlign: 'center',
                backgroundColor: isDragging ? '#eff6ff' : '#f9fafb',
                transition: 'all 0.2s ease',
                cursor: uploading ? 'not-allowed' : 'pointer',
                marginBottom: uploading ? '12px' : '0'
              }}
            >
              <input
                type="file"
                id="fileInput"
                accept="audio/*"
                onChange={handleUpload}
                disabled={uploading}
                style={{
                  position: 'absolute',
                  width: '100%',
                  height: '100%',
                  top: 0,
                  left: 0,
                  opacity: 0,
                  cursor: uploading ? 'not-allowed' : 'pointer'
                }}
              />
              <div style={{
                pointerEvents: 'none',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '8px'
              }}>
                <div style={{
                  fontSize: '32px',
                  color: isDragging ? '#3b82f6' : '#9ca3af'
                }}>
                  📁
                </div>
                <p style={{
                  fontSize: '14px',
                  color: isDragging ? '#3b82f6' : '#374151',
                  fontWeight: '500',
                  margin: '0'
                }}>
                  {isDragging
                    ? 'ここにドロップしてください'
                    : 'ファイルをドラッグ＆ドロップ、またはクリックして選択'}
                </p>
                <p style={{
                  fontSize: '12px',
                  color: '#6b7280',
                  margin: '0'
                }}>
                  対応形式: WAV, MP3
                </p>
              </div>
            </div>
            {uploading && (
              <div>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '6px',
                  fontSize: '13px',
                  color: '#6b7280'
                }}>
                  <span>アップロード中...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div style={{
                  width: '100%',
                  height: '8px',
                  backgroundColor: '#e5e7eb',
                  borderRadius: '4px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    width: `${uploadProgress}%`,
                    height: '100%',
                    backgroundColor: '#3b82f6',
                    transition: 'width 0.3s ease'
                  }} />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ファイル一覧 */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '1px solid #e5e7eb',
          padding: '20px',
          marginBottom: '20px'
        }}>
          <h2 style={{
            fontSize: '16px',
            fontWeight: '600',
            color: '#1a1a1a',
            marginBottom: '16px',
            margin: '0 0 16px 0'
          }}>ファイル一覧</h2>

          {/* 検索・フィルターコントロール */}
          <div style={{
            display: 'flex',
            gap: '12px',
            marginBottom: '16px',
            flexWrap: 'wrap',
            alignItems: 'flex-end'
          }}>
            {/* 検索ボックス */}
            <div style={{ flex: '1', minWidth: '200px' }}>
              <label
                htmlFor="searchQuery"
                style={{
                  display: 'block',
                  fontSize: '13px',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '6px'
                }}
              >
                ファイル名検索
              </label>
              <input
                type="text"
                id="searchQuery"
                placeholder="ファイル名を入力..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
              />
            </div>

            {/* ステータスフィルター */}
            <div style={{ minWidth: '150px' }}>
              <label
                htmlFor="statusFilter"
                style={{
                  display: 'block',
                  fontSize: '13px',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '6px'
                }}
              >
                ステータス
              </label>
              <select
                id="statusFilter"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  backgroundColor: 'white'
                }}
              >
                <option value="all">すべて</option>
                <option value="uploaded">アップロード済</option>
                <option value="processing">解析中</option>
                <option value="completed">完了</option>
                <option value="failed">失敗</option>
              </select>
            </div>

            {/* ソート基準 */}
            <div style={{ minWidth: '130px' }}>
              <label
                htmlFor="sortBy"
                style={{
                  display: 'block',
                  fontSize: '13px',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '6px'
                }}
              >
                並び順
              </label>
              <select
                id="sortBy"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as 'date' | 'name')}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  backgroundColor: 'white'
                }}
              >
                <option value="date">日付順</option>
                <option value="name">名前順</option>
              </select>
            </div>

            {/* ソート順序 */}
            <div style={{ minWidth: '110px' }}>
              <label
                htmlFor="sortOrder"
                style={{
                  display: 'block',
                  fontSize: '13px',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '6px'
                }}
              >
                順序
              </label>
              <select
                id="sortOrder"
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  boxSizing: 'border-box',
                  backgroundColor: 'white'
                }}
              >
                <option value="desc">降順</option>
                <option value="asc">昇順</option>
              </select>
            </div>

            {/* クリアボタン */}
            {(searchQuery || statusFilter !== 'all') && (
              <button
                onClick={() => {
                  setSearchQuery('');
                  setStatusFilter('all');
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f3f4f6',
                  color: '#374151',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  cursor: 'pointer',
                  fontWeight: '500',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#e5e7eb'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
              >
                クリア
              </button>
            )}
          </div>

          {/* 検索結果件数 */}
          {!loading && files.length > 0 && (
            <div style={{
              fontSize: '13px',
              color: '#6b7280',
              marginBottom: '12px'
            }}>
              {searchQuery || statusFilter !== 'all' ? (
                <>
                  検索結果: <strong style={{ color: '#1a1a1a' }}>{filteredAndSortedFiles.length}</strong>件
                  {' / 全 '}<strong style={{ color: '#1a1a1a' }}>{files.length}</strong>件
                </>
              ) : (
                <>
                  全 <strong style={{ color: '#1a1a1a' }}>{files.length}</strong>件のファイル
                </>
              )}
            </div>
          )}

          {loading ? (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '32px 0', margin: 0 }}>
              読み込み中...
            </p>
          ) : files.length === 0 ? (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '32px 0', margin: 0 }}>
              ファイルがまだありません。上記からファイルをアップロードしてください。
            </p>
          ) : filteredAndSortedFiles.length === 0 ? (
            <p style={{ color: '#6b7280', textAlign: 'center', padding: '32px 0', margin: 0 }}>
              検索条件に一致するファイルが見つかりませんでした。
            </p>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{
                width: '100%',
                borderCollapse: 'collapse'
              }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <th style={{ padding: '10px 12px', textAlign: 'left', fontWeight: '500', color: '#6b7280', fontSize: '13px' }}>
                      ファイル名
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '500', color: '#6b7280', fontSize: '13px' }}>
                      サンプルレート
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '500', color: '#6b7280', fontSize: '13px' }}>
                      継続時間
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'right', fontWeight: '500', color: '#6b7280', fontSize: '13px' }}>
                      Episode数
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'left', fontWeight: '500', color: '#6b7280', fontSize: '13px' }}>
                      ステータス
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'left', fontWeight: '500', color: '#6b7280', fontSize: '13px' }}>
                      アップロード日時
                    </th>
                    <th style={{ padding: '10px 12px', textAlign: 'center', fontWeight: '500', color: '#6b7280', fontSize: '13px' }}>
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {paginatedFiles.map((file) => (
                    <tr key={file.id} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '12px', color: '#1a1a1a', fontSize: '14px' }}>
                        <span
                          onClick={() => navigate(`/files/${file.id}`)}
                          style={{
                            cursor: 'pointer',
                            color: '#3b82f6',
                            textDecoration: 'underline'
                          }}
                        >
                          {file.original_filename}
                        </span>
                      </td>
                      <td style={{ padding: '12px', color: '#6b7280', fontSize: '13px', textAlign: 'right' }}>
                        {file.sample_rate ? `${file.sample_rate} Hz` : '-'}
                      </td>
                      <td style={{ padding: '12px', color: '#6b7280', fontSize: '13px', textAlign: 'right' }}>
                        {file.duration ? `${file.duration.toFixed(2)} 秒` : '-'}
                      </td>
                      <td style={{ padding: '12px', color: '#6b7280', fontSize: '13px', textAlign: 'right' }}>
                        {file.status === 'completed' && episodeCounts[file.id] !== undefined
                          ? episodeCounts[file.id]
                          : '-'}
                      </td>
                      <td style={{ padding: '12px' }}>
                        <div>
                          <span style={{
                            padding: '4px 10px',
                            borderRadius: '4px',
                            fontSize: '12px',
                            fontWeight: '500',
                            backgroundColor:
                              file.status === 'completed' ? '#d1fae5' :
                              file.status === 'processing' ? '#fef3c7' :
                              file.status === 'failed' ? '#fee2e2' : '#dbeafe',
                            color:
                              file.status === 'completed' ? '#065f46' :
                              file.status === 'processing' ? '#92400e' :
                              file.status === 'failed' ? '#991b1b' : '#1e40af'
                          }}>
                            {file.status}
                          </span>
                          {analyzingFileId === file.id && (
                            <div style={{ marginTop: '8px' }}>
                              <div style={{
                                fontSize: '12px',
                                color: '#6b7280',
                                marginBottom: '4px'
                              }}>
                                {analysisProgress}
                              </div>
                              <div style={{
                                width: '200px',
                                height: '6px',
                                backgroundColor: '#e5e7eb',
                                borderRadius: '3px',
                                overflow: 'hidden'
                              }}>
                                <div style={{
                                  width: `${analysisProgressPercent}%`,
                                  height: '100%',
                                  backgroundColor: '#3b82f6',
                                  transition: 'width 0.3s ease'
                                }} />
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                      <td style={{ padding: '12px', color: '#6b7280', fontSize: '13px' }}>
                        {new Date(file.uploaded_at).toLocaleString('ja-JP')}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <div style={{ display: 'flex', gap: '6px', justifyContent: 'center', flexWrap: 'wrap' }}>
                          {file.status === 'uploaded' && (
                            <button
                              onClick={() => handleAnalyze(file.id)}
                              disabled={analyzingFileId !== null}
                              style={{
                                padding: '6px 12px',
                                backgroundColor: analyzingFileId !== null ? '#9ca3af' : '#3b82f6',
                                color: 'white',
                                border: 'none',
                                borderRadius: '4px',
                                cursor: analyzingFileId !== null ? 'not-allowed' : 'pointer',
                                fontSize: '12px',
                                fontWeight: '500'
                              }}
                            >
                              解析開始
                            </button>
                          )}
                          {file.status === 'completed' && (
                            <>
                              <button
                                onClick={() => navigate(`/files/${file.id}`)}
                                style={{
                                  padding: '6px 12px',
                                  backgroundColor: '#10b981',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  fontSize: '12px',
                                  fontWeight: '500'
                                }}
                              >
                                詳細表示
                              </button>
                              <button
                                onClick={() => handleExport(file.id, 'excel')}
                                style={{
                                  padding: '6px 12px',
                                  backgroundColor: '#6b7280',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  fontSize: '12px',
                                  fontWeight: '500'
                                }}
                              >
                                Excel
                              </button>
                              <button
                                onClick={() => handleExport(file.id, 'pdf')}
                                style={{
                                  padding: '6px 12px',
                                  backgroundColor: '#6b7280',
                                  color: 'white',
                                  border: 'none',
                                  borderRadius: '4px',
                                  cursor: 'pointer',
                                  fontSize: '12px',
                                  fontWeight: '500'
                                }}
                              >
                                PDF
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => handleDelete(file.id, file.original_filename)}
                            style={{
                              padding: '6px 12px',
                              backgroundColor: '#dc2626',
                              color: 'white',
                              border: 'none',
                              borderRadius: '4px',
                              cursor: 'pointer',
                              fontSize: '12px',
                              fontWeight: '500'
                            }}
                          >
                            削除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* ページネーション */}
              {totalPages > 1 && (
                <div style={{
                  display: 'flex',
                  justifyContent: 'center',
                  alignItems: 'center',
                  gap: '8px',
                  marginTop: '20px',
                  paddingTop: '20px',
                  borderTop: '1px solid #e5e7eb'
                }}>
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: currentPage === 1 ? '#f3f4f6' : '#3b82f6',
                      color: currentPage === 1 ? '#9ca3af' : 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: currentPage === 1 ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: '500',
                      transition: 'background-color 0.2s'
                    }}
                  >
                    前へ
                  </button>

                  <div style={{
                    display: 'flex',
                    gap: '4px',
                    alignItems: 'center'
                  }}>
                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => {
                      // 現在のページ周辺のみ表示（最初、最後、現在±2ページ）
                      const shouldShow =
                        page === 1 ||
                        page === totalPages ||
                        (page >= currentPage - 2 && page <= currentPage + 2);

                      const shouldShowEllipsisBefore = page === currentPage - 3 && currentPage > 4;
                      const shouldShowEllipsisAfter = page === currentPage + 3 && currentPage < totalPages - 3;

                      if (shouldShowEllipsisBefore || shouldShowEllipsisAfter) {
                        return (
                          <span
                            key={page}
                            style={{
                              padding: '8px 4px',
                              color: '#6b7280',
                              fontSize: '14px'
                            }}
                          >
                            ...
                          </span>
                        );
                      }

                      if (!shouldShow) return null;

                      return (
                        <button
                          key={page}
                          onClick={() => setCurrentPage(page)}
                          style={{
                            padding: '8px 12px',
                            backgroundColor: currentPage === page ? '#3b82f6' : 'white',
                            color: currentPage === page ? 'white' : '#374151',
                            border: currentPage === page ? 'none' : '1px solid #d1d5db',
                            borderRadius: '6px',
                            cursor: 'pointer',
                            fontSize: '14px',
                            fontWeight: currentPage === page ? '600' : '500',
                            minWidth: '36px',
                            transition: 'all 0.2s'
                          }}
                          onMouseOver={(e) => {
                            if (currentPage !== page) {
                              e.currentTarget.style.backgroundColor = '#f3f4f6';
                            }
                          }}
                          onMouseOut={(e) => {
                            if (currentPage !== page) {
                              e.currentTarget.style.backgroundColor = 'white';
                            }
                          }}
                        >
                          {page}
                        </button>
                      );
                    })}
                  </div>

                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    style={{
                      padding: '8px 12px',
                      backgroundColor: currentPage === totalPages ? '#f3f4f6' : '#3b82f6',
                      color: currentPage === totalPages ? '#9ca3af' : 'white',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: currentPage === totalPages ? 'not-allowed' : 'pointer',
                      fontSize: '14px',
                      fontWeight: '500',
                      transition: 'background-color 0.2s'
                    }}
                  >
                    次へ
                  </button>

                  <div style={{
                    marginLeft: '12px',
                    fontSize: '13px',
                    color: '#6b7280'
                  }}>
                    {currentPage} / {totalPages} ページ
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 解析結果表示 */}
        {analysisResult && selectedFile && (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            padding: '20px',
            width: '100%',
            boxSizing: 'border-box'
          }}>
            <div style={{ marginBottom: '20px' }}>
              <h2 style={{
                fontSize: '16px',
                fontWeight: '600',
                color: '#1a1a1a',
                marginBottom: '4px',
                margin: '0 0 4px 0'
              }}>解析結果</h2>
              <p style={{ color: '#6b7280', fontSize: '13px', margin: 0 }}>
                {selectedFile.original_filename}
              </p>
            </div>

            {/* 音声プレーヤー */}
            <AudioPlayer
              fileId={selectedFile.id}
              filename={selectedFile.original_filename}
              cryEpisodes={analysisResult.result_data.cry_episodes}
              token={localStorage.getItem('token') || ''}
            />

            {/* 統計サマリー */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '12px',
              marginBottom: '20px'
            }}>
              <div style={{
                padding: '16px',
                backgroundColor: '#f9fafb',
                borderRadius: '6px',
                border: '1px solid #e5e7eb'
              }}>
                <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
                  検出エピソード数
                </div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#1a1a1a' }}>
                  {analysisResult.result_data.cry_episodes.length}
                </div>
              </div>
              <div style={{
                padding: '16px',
                backgroundColor: '#f9fafb',
                borderRadius: '6px',
                border: '1px solid #e5e7eb'
              }}>
                <div style={{ fontSize: '12px', color: '#6b7280', marginBottom: '4px' }}>
                  総泣き時間
                </div>
                <div style={{ fontSize: '24px', fontWeight: '600', color: '#1a1a1a' }}>
                  {analysisResult.result_data.cry_episodes
                    .reduce((sum, ep) => sum + ep.duration, 0)
                    .toFixed(2)} 秒
                </div>
              </div>
            </div>

            {/* エピソード一覧 */}
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#1a1a1a',
              marginBottom: '12px',
              margin: '0 0 12px 0'
            }}>泣き声エピソード</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <th style={{ padding: '8px 10px', textAlign: 'center', fontSize: '12px', fontWeight: '500', color: '#6b7280' }}>
                      No.
                    </th>
                    <th style={{ padding: '8px 10px', textAlign: 'right', fontSize: '12px', fontWeight: '500', color: '#6b7280' }}>
                      開始時刻 (秒)
                    </th>
                    <th style={{ padding: '8px 10px', textAlign: 'right', fontSize: '12px', fontWeight: '500', color: '#6b7280' }}>
                      終了時刻 (秒)
                    </th>
                    <th style={{ padding: '8px 10px', textAlign: 'right', fontSize: '12px', fontWeight: '500', color: '#6b7280' }}>
                      継続時間 (秒)
                    </th>
                    <th style={{ padding: '8px 10px', textAlign: 'right', fontSize: '12px', fontWeight: '500', color: '#6b7280' }}>
                      信頼度
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {analysisResult.result_data.cry_episodes.map((episode, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '10px', textAlign: 'center', color: '#1a1a1a', fontSize: '13px' }}>
                        {idx + 1}
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right', color: '#1a1a1a', fontSize: '13px' }}>
                        {episode.start_time.toFixed(3)}
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right', color: '#1a1a1a', fontSize: '13px' }}>
                        {episode.end_time.toFixed(3)}
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right', color: '#1a1a1a', fontSize: '13px' }}>
                        {episode.duration.toFixed(3)}
                      </td>
                      <td style={{ padding: '10px', textAlign: 'right', color: '#1a1a1a', fontSize: '13px' }}>
                        {episode.confidence.toFixed(4)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* 可視化セクション */}
            <div style={{ marginTop: '30px' }}>
              <h3 style={{
                fontSize: '14px',
                fontWeight: '600',
                color: '#1a1a1a',
                marginBottom: '16px',
                margin: '0 0 16px 0'
              }}>波形・スペクトログラム</h3>

              {/* 波形表示 */}
              <div style={{ marginBottom: '24px' }}>
                <h4 style={{
                  fontSize: '13px',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '12px',
                  margin: '0 0 12px 0'
                }}>波形</h4>
                <WaveformVisualization
                  fileId={selectedFile.id}
                  height={300}
                />
              </div>

              {/* スペクトログラム表示 */}
              <div style={{ marginBottom: '24px' }}>
                <h4 style={{
                  fontSize: '13px',
                  fontWeight: '500',
                  color: '#374151',
                  marginBottom: '12px',
                  margin: '0 0 12px 0'
                }}>スペクトログラム</h4>
                <SpectrogramVisualization
                  fileId={selectedFile.id}
                  height={400}
                />
              </div>
            </div>

            {/* エクスポートボタンセクション（既存のまま維持） */}
            <div style={{
              marginTop: '24px',
              paddingTop: '20px',
              borderTop: '1px solid #e5e7eb',
              display: 'flex',
              gap: '12px',
              flexWrap: 'wrap'
            }}>
              <a
                href={exportAPI.episodesCSV(selectedFile.id)}
                download
                style={{
                  padding: '10px 16px',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  textDecoration: 'none',
                  display: 'inline-block'
                }}
              >
                CSV出力
              </a>
              <a
                href={exportAPI.excel(selectedFile.id)}
                download
                style={{
                  padding: '10px 16px',
                  backgroundColor: '#10b981',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  textDecoration: 'none',
                  display: 'inline-block'
                }}
              >
                Excel出力
              </a>
              <a
                href={exportAPI.pdf(selectedFile.id)}
                download
                style={{
                  padding: '10px 16px',
                  backgroundColor: '#ef4444',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500',
                  textDecoration: 'none',
                  display: 'inline-block'
                }}
              >
                PDF出力
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardPage;
