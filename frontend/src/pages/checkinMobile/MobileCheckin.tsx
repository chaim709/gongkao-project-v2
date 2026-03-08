import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
});

interface CheckinInfo {
  title: string;
  expires_at: string;
}

interface CheckinResult {
  success: boolean;
  student_name: string;
  message: string;
  duplicate: boolean;
}

type Step = 'loading' | 'phone' | 'result' | 'error';

export default function MobileCheckin() {
  const { token } = useParams<{ token: string }>();
  const [step, setStep] = useState<Step>('loading');
  const [info, setInfo] = useState<CheckinInfo | null>(null);
  const [phone, setPhone] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<CheckinResult | null>(null);

  // 获取签到信息
  useEffect(() => {
    api.get(`/checkin-codes/${token}/info`)
      .then(res => {
        setInfo(res.data);
        setStep('phone');
      })
      .catch(err => {
        setError(err?.response?.data?.detail || '签到码无效或已过期');
        setStep('error');
      });
  }, [token]);

  const handleSubmit = async () => {
    if (!/^1\d{10}$/.test(phone)) {
      setError('请输入正确的11位手机号');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const res = await api.post(`/checkin-codes/${token}/submit`, { phone });
      setResult(res.data);
      setStep('result');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr?.response?.data?.detail || '签到失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>✅ 课堂签到</h1>
        {info && <p style={styles.subtitle}>{info.title}</p>}
      </div>

      {error && step !== 'error' && <div style={styles.errorBox}>{error}</div>}

      {step === 'loading' && (
        <div style={styles.card}>
          <p style={{ textAlign: 'center', color: '#999' }}>加载签到信息中...</p>
        </div>
      )}

      {step === 'error' && (
        <div style={styles.card}>
          <div style={{ textAlign: 'center', fontSize: 48, marginBottom: 16 }}>❌</div>
          <h2 style={{ ...styles.cardTitle, textAlign: 'center' as const }}>{error}</h2>
          <p style={{ textAlign: 'center', color: '#999' }}>请联系老师获取新的签到码</p>
        </div>
      )}

      {step === 'phone' && (
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>输入手机号签到</h2>
          <p style={styles.hint}>请输入报名时预留的手机号</p>
          <input
            type="tel"
            placeholder="请输入手机号"
            value={phone}
            onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))}
            style={styles.input}
            maxLength={11}
          />
          <button
            onClick={handleSubmit}
            disabled={loading || phone.length !== 11}
            style={{
              ...styles.button,
              opacity: loading || phone.length !== 11 ? 0.6 : 1,
            }}
          >
            {loading ? '签到中...' : '立即签到'}
          </button>
        </div>
      )}

      {step === 'result' && result && (
        <div style={styles.card}>
          <div style={{ textAlign: 'center', fontSize: 64, marginBottom: 16 }}>
            {result.duplicate ? '⚠️' : '🎉'}
          </div>
          <h2 style={{ ...styles.cardTitle, textAlign: 'center' as const }}>
            {result.duplicate ? '已签到' : '签到成功'}
          </h2>
          <p style={{ textAlign: 'center', fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
            {result.student_name} 同学
          </p>
          <p style={{ textAlign: 'center', color: '#999' }}>{result.message}</p>
          <p style={{ textAlign: 'center', color: '#bbb', fontSize: 13, marginTop: 16 }}>
            {new Date().toLocaleString('zh-CN')}
          </p>
        </div>
      )}

      <p style={styles.footer}>公考管理系统</p>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #52c41a 0%, #1890ff 100%)',
    padding: '20px 16px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    textAlign: 'center',
    marginBottom: 24,
  },
  title: {
    color: '#fff',
    fontSize: 24,
    margin: 0,
  },
  subtitle: {
    color: 'rgba(255,255,255,0.9)',
    fontSize: 16,
    marginTop: 4,
  },
  card: {
    background: '#fff',
    borderRadius: 16,
    padding: '32px 24px',
    boxShadow: '0 8px 24px rgba(0,0,0,0.12)',
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: 600,
    margin: '0 0 12px 0',
    color: '#333',
  },
  hint: {
    color: '#999',
    fontSize: 14,
    margin: '0 0 16px 0',
  },
  input: {
    width: '100%',
    padding: '14px 16px',
    fontSize: 18,
    border: '2px solid #d9d9d9',
    borderRadius: 12,
    marginBottom: 20,
    outline: 'none',
    boxSizing: 'border-box',
    textAlign: 'center',
    letterSpacing: 2,
  },
  button: {
    width: '100%',
    padding: '14px 0',
    fontSize: 18,
    fontWeight: 600,
    color: '#fff',
    background: 'linear-gradient(135deg, #52c41a 0%, #1890ff 100%)',
    border: 'none',
    borderRadius: 12,
    cursor: 'pointer',
  },
  errorBox: {
    background: '#fff2f0',
    border: '1px solid #ffccc7',
    borderRadius: 12,
    padding: '12px 16px',
    color: '#ff4d4f',
    fontSize: 14,
    marginBottom: 16,
    textAlign: 'center',
  },
  footer: {
    textAlign: 'center',
    color: 'rgba(255,255,255,0.5)',
    fontSize: 12,
    marginTop: 32,
  },
};
