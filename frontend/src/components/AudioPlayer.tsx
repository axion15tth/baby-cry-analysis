import React, { useRef, useState, useEffect } from 'react';

interface CryEpisode {
  start_time: number;
  end_time: number;
  duration: number;
  confidence: number;
}

interface AudioPlayerProps {
  fileId: number;
  filename: string;
  cryEpisodes?: CryEpisode[];
  token: string;
}

const AudioPlayer: React.FC<AudioPlayerProps> = ({ fileId, filename, cryEpisodes = [], token }) => {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [selectedEpisode, setSelectedEpisode] = useState<number | null>(null);

  const audioUrl = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/audio-files/${fileId}/stream`;

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const updateTime = () => setCurrentTime(audio.currentTime);
    const updateDuration = () => setDuration(audio.duration);
    const handleEnded = () => {
      setIsPlaying(false);
      // エピソード再生終了時に停止
      if (selectedEpisode !== null) {
        setSelectedEpisode(null);
      }
    };

    audio.addEventListener('timeupdate', updateTime);
    audio.addEventListener('loadedmetadata', updateDuration);
    audio.addEventListener('ended', handleEnded);

    return () => {
      audio.removeEventListener('timeupdate', updateTime);
      audio.removeEventListener('loadedmetadata', updateDuration);
      audio.removeEventListener('ended', handleEnded);
    };
  }, [selectedEpisode]);

  // エピソード再生時の時間チェック
  useEffect(() => {
    if (selectedEpisode !== null && audioRef.current && cryEpisodes[selectedEpisode]) {
      const episode = cryEpisodes[selectedEpisode];
      if (currentTime >= episode.end_time) {
        audioRef.current.pause();
        setIsPlaying(false);
        setSelectedEpisode(null);
      }
    }
  }, [currentTime, selectedEpisode, cryEpisodes]);

  const togglePlayPause = () => {
    const audio = audioRef.current;
    if (!audio) return;

    if (isPlaying) {
      audio.pause();
    } else {
      audio.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;

    const time = parseFloat(e.target.value);
    audio.currentTime = time;
    setCurrentTime(time);
  };

  const playEpisode = (index: number) => {
    const audio = audioRef.current;
    if (!audio) return;

    const episode = cryEpisodes[index];
    audio.currentTime = episode.start_time;
    audio.play();
    setIsPlaying(true);
    setSelectedEpisode(index);
  };

  const formatTime = (seconds: number): string => {
    if (!isFinite(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getProgressPercentage = () => {
    if (!duration) return 0;
    return (currentTime / duration) * 100;
  };

  // エピソードの位置を計算（プログレスバー上）
  const getEpisodePosition = (episode: CryEpisode) => {
    if (!duration) return { left: 0, width: 0 };
    return {
      left: (episode.start_time / duration) * 100,
      width: ((episode.end_time - episode.start_time) / duration) * 100
    };
  };

  return (
    <div className="audio-player">
      <audio
        ref={audioRef}
        src={audioUrl}
        preload="metadata"
      />

      <div className="player-header">
        <h4>音声ファイル: {filename}</h4>
      </div>

      <div className="player-controls">
        <button
          onClick={togglePlayPause}
          className="play-button"
          disabled={!duration}
        >
          {isPlaying ? '⏸' : '▶'}
        </button>

        <span className="time">{formatTime(currentTime)}</span>

        <div className="progress-container">
          {/* プログレスバー */}
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${getProgressPercentage()}%` }}
            />

            {/* Cry Episodesの表示 */}
            {cryEpisodes.map((episode, index) => {
              const pos = getEpisodePosition(episode);
              return (
                <div
                  key={index}
                  className={`episode-marker ${selectedEpisode === index ? 'selected' : ''}`}
                  style={{
                    left: `${pos.left}%`,
                    width: `${pos.width}%`
                  }}
                  title={`Episode ${index + 1}: ${formatTime(episode.start_time)} - ${formatTime(episode.end_time)}`}
                />
              );
            })}
          </div>

          {/* シークバー */}
          <input
            type="range"
            min="0"
            max={duration || 0}
            value={currentTime}
            onChange={handleSeek}
            className="seek-bar"
            disabled={!duration}
          />
        </div>

        <span className="time">{formatTime(duration)}</span>
      </div>

      {/* Cry Episodes リスト */}
      {cryEpisodes.length > 0 && (
        <div className="episodes-list">
          <h5>Cry Episodes ({cryEpisodes.length})</h5>
          <div className="episodes-grid">
            {cryEpisodes.map((episode, index) => (
              <button
                key={index}
                onClick={() => playEpisode(index)}
                className={`episode-button ${selectedEpisode === index ? 'active' : ''}`}
              >
                <span className="episode-number">#{index + 1}</span>
                <span className="episode-time">
                  {formatTime(episode.start_time)} - {formatTime(episode.end_time)}
                </span>
                <span className="episode-duration">
                  {episode.duration.toFixed(2)}s
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      <style>{`
        .audio-player {
          background: white;
          border-radius: 8px;
          padding: 20px;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
          margin: 20px 0;
        }

        .player-header h4 {
          margin: 0 0 15px 0;
          font-size: 16px;
          color: #333;
        }

        .player-controls {
          display: flex;
          align-items: center;
          gap: 15px;
        }

        .play-button {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          border: none;
          background: #007bff;
          color: white;
          font-size: 20px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: background 0.3s;
        }

        .play-button:hover:not(:disabled) {
          background: #0056b3;
        }

        .play-button:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .time {
          font-size: 14px;
          color: #666;
          min-width: 45px;
        }

        .progress-container {
          flex: 1;
          position: relative;
          height: 40px;
          display: flex;
          align-items: center;
        }

        .progress-bar {
          position: absolute;
          top: 50%;
          left: 0;
          right: 0;
          height: 8px;
          background: #e0e0e0;
          border-radius: 4px;
          transform: translateY(-50%);
          overflow: visible;
        }

        .progress-fill {
          height: 100%;
          background: #007bff;
          border-radius: 4px;
          transition: width 0.1s;
        }

        .episode-marker {
          position: absolute;
          top: 0;
          height: 100%;
          background: rgba(255, 193, 7, 0.5);
          border: 1px solid rgba(255, 193, 7, 0.8);
          border-radius: 4px;
          pointer-events: none;
        }

        .episode-marker.selected {
          background: rgba(76, 175, 80, 0.5);
          border-color: rgba(76, 175, 80, 0.8);
        }

        .seek-bar {
          position: absolute;
          top: 50%;
          left: 0;
          right: 0;
          transform: translateY(-50%);
          width: 100%;
          height: 24px;
          opacity: 0;
          cursor: pointer;
        }

        .seek-bar:hover {
          opacity: 0.1;
        }

        .episodes-list {
          margin-top: 20px;
          padding-top: 20px;
          border-top: 1px solid #e0e0e0;
        }

        .episodes-list h5 {
          margin: 0 0 15px 0;
          font-size: 14px;
          color: #666;
          font-weight: 600;
        }

        .episodes-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 10px;
        }

        .episode-button {
          padding: 12px;
          border: 1px solid #e0e0e0;
          border-radius: 6px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          gap: 4px;
        }

        .episode-button:hover {
          background: #f5f5f5;
          border-color: #007bff;
        }

        .episode-button.active {
          background: #e3f2fd;
          border-color: #007bff;
        }

        .episode-number {
          font-weight: 600;
          color: #007bff;
          font-size: 12px;
        }

        .episode-time {
          font-size: 13px;
          color: #666;
        }

        .episode-duration {
          font-size: 12px;
          color: #999;
        }
      `}</style>
    </div>
  );
};

export default AudioPlayer;
