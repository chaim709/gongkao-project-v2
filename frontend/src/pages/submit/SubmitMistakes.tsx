import { useState } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
});

interface SubmitResult {
  success: boolean;
  student_name: string;
  paper_title: string;
  total: number;
  correct: number;
  wrong: number;
  accuracy: number;
  weakest_areas: string;
  message: string;
}

type Step = 'phone' | 'select' | 'confirm' | 'result';

export default function SubmitMistakes() {
  const { token } = useParams<{ token: string }>();
  const [step, setStep] = useState<Step>('phone');
  const [phone, setPhone] = useState('');
  const [totalQuestions, setTotalQuestions] = useState(0);
  const [wrongNumbers, setWrongNumbers] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [paperInfo, setPaperInfo] = useState<{ title: string; total_questions: number; subject: string } | null>(null);

  // 验证手机号并获取试卷信息
  const handlePhoneSubmit = async () => {
    if (!/^1\d{10}$/.test(phone)) {
      setError('请输入正确的11位手机号');
      return;
    }
    setError('');
    setLoading(true);
    try {
      // 先提交一次空数据来验证 token 和获取试卷信息
      // 但这样不好，我们直接进入选题页面，提交时再验证
      // 通过 token 获取试卷基本信息 — 不需要后端新接口，用前端输入题数
      setStep('select');
    } catch {
      setError('系统错误，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 切换题号
  const toggleQuestion = (num: number) => {
    setWrongNumbers(prev => {
      const next = new Set(prev);
      if (next.has(num)) {
        next.delete(num);
      } else {
        next.add(num);
      }
      return next;
    });
  };

  // 提交
  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await api.post(`/exams/submit/${token}`, {
        phone,
        wrong_numbers: Array.from(wrongNumbers).sort((a, b) => a - b),
      });
      setResult(res.data);
      setPaperInfo({ title: res.data.paper_title, total_questions: res.data.total, subject: '' });
      setStep('result');
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { detail?: string } } };
      setError(axiosErr?.response?.data?.detail || '提交失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>📝 错题提交</h1>
        {paperInfo && <p style={styles.subtitle}>{paperInfo.title}</p>}
      </div>

      {error && <div style={styles.error}>{error}</div>}

      {/* Step 1: 输入手机号 */}
      {step === 'phone' && (
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>验证身份</h2>
          <p style={styles.hint}>请输入报名时预留的手机号</p>
          <input
            type="tel"
            placeholder="请输入手机号"
            value={phone}
            onChange={e => setPhone(e.target.value.replace(/\D/g, '').slice(0, 11))}
            style={styles.input}
            maxLength={11}
          />
          <p style={styles.hint}>请输入试卷总题数</p>
          <input
            type="number"
            placeholder="如：120"
            value={totalQuestions || ''}
            onChange={e => setTotalQuestions(Math.min(300, Math.max(0, parseInt(e.target.value) || 0)))}
            style={styles.input}
          />
          <button
            onClick={handlePhoneSubmit}
            disabled={loading || !phone || !totalQuestions}
            style={{
              ...styles.button,
              opacity: loading || !phone || !totalQuestions ? 0.6 : 1,
            }}
          >
            {loading ? '验证中...' : '下一步'}
          </button>
        </div>
      )}

      {/* Step 2: 选择错题 */}
      {step === 'select' && (
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>选择错题题号</h2>
          <p style={styles.hint}>
            点击题号标记为错题（红色），已选 <strong style={{ color: '#ff4d4f' }}>{wrongNumbers.size}</strong> 题
          </p>

          <div style={styles.grid}>
            {Array.from({ length: totalQuestions }, (_, i) => i + 1).map(num => (
              <button
                key={num}
                onClick={() => toggleQuestion(num)}
                style={{
                  ...styles.numBtn,
                  backgroundColor: wrongNumbers.has(num) ? '#ff4d4f' : '#f5f5f5',
                  color: wrongNumbers.has(num) ? '#fff' : '#333',
                  borderColor: wrongNumbers.has(num) ? '#ff4d4f' : '#e8e8e8',
                }}
              >
                {num}
              </button>
            ))}
          </div>

          <div style={styles.actions}>
            <button onClick={() => setStep('phone')} style={styles.backBtn}>返回</button>
            <button
              onClick={() => setStep('confirm')}
              style={styles.button}
            >
              确认提交 ({wrongNumbers.size}题)
            </button>
          </div>
        </div>
      )}

      {/* Step 3: 确认 */}
      {step === 'confirm' && (
        <div style={styles.card}>
          <h2 style={styles.cardTitle}>确认提交</h2>
          <div style={styles.summary}>
            <p>手机号：{phone.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2')}</p>
            <p>总题数：{totalQuestions} 题</p>
            <p>错题数：<span style={{ color: '#ff4d4f', fontWeight: 'bold' }}>{wrongNumbers.size}</span> 题</p>
            <p>正确率：<span style={{ color: '#52c41a', fontWeight: 'bold' }}>
              {((totalQuestions - wrongNumbers.size) / totalQuestions * 100).toFixed(1)}%
            </span></p>
            {wrongNumbers.size > 0 && (
              <p style={{ fontSize: 13, color: '#999' }}>
                错题题号：{Array.from(wrongNumbers).sort((a, b) => a - b).join('、')}
              </p>
            )}
          </div>
          <div style={styles.actions}>
            <button onClick={() => setStep('select')} style={styles.backBtn}>返回修改</button>
            <button onClick={handleSubmit} disabled={loading} style={{
              ...styles.button,
              opacity: loading ? 0.6 : 1,
            }}>
              {loading ? '提交中...' : '确认提交'}
            </button>
          </div>
        </div>
      )}

      {/* Step 4: 结果 */}
      {step === 'result' && result && (
        <div style={styles.card}>
          <div style={styles.resultIcon}>✅</div>
          <h2 style={{ ...styles.cardTitle, textAlign: 'center' as const }}>提交成功</h2>
          <div style={styles.resultCard}>
            <p style={styles.resultName}>{result.student_name} 同学</p>
            <p style={styles.resultPaper}>{result.paper_title}</p>
            <div style={styles.statsRow}>
              <div style={styles.statItem}>
                <span style={styles.statValue}>{result.total}</span>
                <span style={styles.statLabel}>总题</span>
              </div>
              <div style={styles.statItem}>
                <span style={{ ...styles.statValue, color: '#52c41a' }}>{result.correct}</span>
                <span style={styles.statLabel}>正确</span>
              </div>
              <div style={styles.statItem}>
                <span style={{ ...styles.statValue, color: '#ff4d4f' }}>{result.wrong}</span>
                <span style={styles.statLabel}>错误</span>
              </div>
              <div style={styles.statItem}>
                <span style={{ ...styles.statValue, color: '#1890ff' }}>{result.accuracy}%</span>
                <span style={styles.statLabel}>正确率</span>
              </div>
            </div>
          </div>
          {result.weakest_areas !== '无' && (
            <div style={styles.weakArea}>
              <p style={styles.weakTitle}>⚠️ 薄弱模块</p>
              <p style={styles.weakText}>{result.weakest_areas}</p>
            </div>
          )}
          <p style={styles.tipText}>结果已同步到老师后台，请继续加油！</p>
        </div>
      )}

      <p style={styles.footer}>公考管理系统</p>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    padding: '20px 16px',
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
  },
  header: {
    textAlign: 'center',
    marginBottom: 20,
  },
  title: {
    color: '#fff',
    fontSize: 24,
    margin: 0,
  },
  subtitle: {
    color: 'rgba(255,255,255,0.85)',
    fontSize: 14,
    marginTop: 4,
  },
  card: {
    background: '#fff',
    borderRadius: 12,
    padding: '24px 20px',
    marginBottom: 16,
    boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 600,
    margin: '0 0 12px 0',
    color: '#333',
  },
  hint: {
    color: '#999',
    fontSize: 14,
    margin: '0 0 12px 0',
  },
  input: {
    width: '100%',
    padding: '12px 16px',
    fontSize: 16,
    border: '1px solid #d9d9d9',
    borderRadius: 8,
    marginBottom: 16,
    outline: 'none',
    boxSizing: 'border-box',
  },
  button: {
    width: '100%',
    padding: '12px 0',
    fontSize: 16,
    fontWeight: 600,
    color: '#fff',
    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
  },
  backBtn: {
    flex: 1,
    padding: '12px 0',
    fontSize: 14,
    color: '#666',
    background: '#f5f5f5',
    border: 'none',
    borderRadius: 8,
    cursor: 'pointer',
  },
  error: {
    background: '#fff2f0',
    border: '1px solid #ffccc7',
    borderRadius: 8,
    padding: '10px 16px',
    color: '#ff4d4f',
    fontSize: 14,
    marginBottom: 16,
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(6, 1fr)',
    gap: 8,
    marginBottom: 20,
    maxHeight: 400,
    overflowY: 'auto',
  },
  numBtn: {
    width: '100%',
    aspectRatio: '1',
    border: '1px solid',
    borderRadius: 8,
    fontSize: 14,
    fontWeight: 500,
    cursor: 'pointer',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'all 0.15s',
  },
  actions: {
    display: 'flex',
    gap: 12,
  },
  summary: {
    background: '#fafafa',
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
    lineHeight: 2,
  },
  resultIcon: {
    textAlign: 'center',
    fontSize: 48,
    marginBottom: 8,
  },
  resultCard: {
    background: '#fafafa',
    borderRadius: 8,
    padding: 16,
    textAlign: 'center',
    marginBottom: 16,
  },
  resultName: {
    fontSize: 18,
    fontWeight: 600,
    margin: '0 0 4px 0',
  },
  resultPaper: {
    fontSize: 13,
    color: '#999',
    margin: '0 0 16px 0',
  },
  statsRow: {
    display: 'flex',
    justifyContent: 'space-around',
  },
  statItem: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: 700,
  },
  statLabel: {
    fontSize: 12,
    color: '#999',
    marginTop: 2,
  },
  weakArea: {
    background: '#fffbe6',
    border: '1px solid #ffe58f',
    borderRadius: 8,
    padding: '12px 16px',
    marginBottom: 16,
  },
  weakTitle: {
    fontSize: 14,
    fontWeight: 600,
    margin: '0 0 4px 0',
  },
  weakText: {
    fontSize: 13,
    color: '#d48806',
    margin: 0,
  },
  tipText: {
    textAlign: 'center',
    color: '#999',
    fontSize: 13,
  },
  footer: {
    textAlign: 'center',
    color: 'rgba(255,255,255,0.5)',
    fontSize: 12,
    marginTop: 24,
  },
};
