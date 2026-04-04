// ============================================================
// Supabase Edge Function: check-answer
// 역할: 클라이언트가 제출한 답을 검증하고 해설을 반환
//       answers 테이블은 service_role 키로만 접근 → anon 직접 접근 불가
// ============================================================

import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'  // supabase JS 클라이언트 임포트

// 허용할 Origin (배포 URL로 변경 가능)
const ALLOWED_ORIGIN = 'https://animated-lebkuchen-638396.netlify.app'  // CORS 허용 도메인

const corsHeaders = {
  'Access-Control-Allow-Origin': ALLOWED_ORIGIN,           // 이 도메인에서 온 요청만 허용
  'Access-Control-Allow-Headers': 'content-type',          // 허용 헤더
  'Access-Control-Allow-Methods': 'POST, OPTIONS',         // 허용 메서드
}

// ── 간단한 Rate Limiter (메모리 기반, 함수 인스턴스 내) ─────────────
// Edge Function은 요청마다 새 인스턴스일 수 있으므로
// 완전한 rate limit는 Upstash Redis 등 외부 저장소 필요
// 여기서는 같은 인스턴스 내 연속 요청을 제한 (학습용 구현)
const requestCounts = new Map<string, { count: number; resetAt: number }>()

function isRateLimited(userId: string): boolean {
  const now = Date.now()                                    // 현재 시각 (ms)
  const window = 60_000                                     // 1분 윈도우
  const maxRequests = 120                                   // 1분에 최대 120회 (문제당 1회)

  const entry = requestCounts.get(userId)

  if (!entry || now > entry.resetAt) {
    requestCounts.set(userId, { count: 1, resetAt: now + window })  // 새 윈도우 시작
    return false
  }

  if (entry.count >= maxRequests) return true              // 한도 초과

  entry.count++                                            // 카운트 증가
  return false
}

// ── 메인 핸들러 ────────────────────────────────────────────────
Deno.serve(async (req: Request) => {

  // OPTIONS preflight 요청 처리 (CORS 브라우저 사전 확인)
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  // POST 이외 메서드 거부
  if (req.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }

  try {
    // ── 요청 바디 파싱 ──────────────────────────────────────────
    const { question_id, chosen_answer, user_id } = await req.json()

    // 필수 필드 검증
    if (!question_id || !chosen_answer || !user_id) {
      return new Response(JSON.stringify({ error: 'question_id, chosen_answer, user_id 필수' }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    // ── Rate Limit 체크 ─────────────────────────────────────────
    if (isRateLimited(String(user_id))) {
      return new Response(JSON.stringify({ error: '요청이 너무 많습니다. 잠시 후 다시 시도하세요.' }), {
        status: 429,                                       // Too Many Requests
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    // ── Supabase 클라이언트 (SERVICE_ROLE_KEY 사용) ─────────────
    // SERVICE_ROLE_KEY는 RLS를 우회 → answers 테이블 접근 가능
    // 이 키는 절대 브라우저에 노출되지 않음 (Edge Function 환경변수)
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL')!,                       // 환경변수에서 URL 읽기
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!           // 환경변수에서 서비스 키 읽기
    )

    // ── answers 테이블에서 정답 조회 ────────────────────────────
    const { data: answer, error } = await supabase
      .from('answers')
      .select('correct_option, explanation, detail')       // 정답 + 해설 + 보기별 풀이
      .eq('question_id', question_id)                      // 해당 문제 ID 조건
      .single()                                            // 1행만 반환

    if (error || !answer) {
      return new Response(JSON.stringify({ error: '문제를 찾을 수 없습니다' }), {
        status: 404,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    // ── 정답 여부 판정 ───────────────────────────────────────────
    const is_correct = answer.correct_option === Number(chosen_answer)  // 제출 답 vs 정답 비교

    // ── 결과 반환 (정답·해설 포함) ──────────────────────────────
    return new Response(
      JSON.stringify({
        is_correct,                                        // true / false
        correct_option: answer.correct_option,             // 정답 번호
        explanation: answer.explanation,                   // 정답 해설
        detail: answer.detail ?? [],                       // 보기별 풀이 배열
      }),
      {
        status: 200,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )

  } catch (err) {
    console.error('check-answer error:', err)
    return new Response(JSON.stringify({ error: '서버 오류가 발생했습니다' }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})
