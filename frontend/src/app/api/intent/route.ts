import { NextResponse } from 'next/server';

const endpoint = process.env.AZURE_OPENAI_ENDPOINT ?? '';
const apiKey = process.env.AZURE_OPENAI_API_KEY ?? '';
const apiVersion = process.env.AZURE_OPENAI_API_VERSION ?? '2024-12-01-preview';
const deployment = process.env.AZURE_OPENAI_DEPLOYMENT_NAME ?? 'gpt-5.1-chat';

export async function POST(request: Request) {
  const { message } = (await request.json()) as { message?: string };

  if (!message) {
    return NextResponse.json({ intent: '', confidence: 0, raw: 'Missing message' }, { status: 400 });
  }

  if (!endpoint || !apiKey) {
    return NextResponse.json({
      intent: 'unconfigured',
      confidence: 0,
      raw: 'Azure OpenAI not configured',
    });
  }

  const url = `${endpoint.replace(/\\/$/, '')}/openai/deployments/${deployment}/chat/completions?api-version=${apiVersion}`;
  const payload = {
    messages: [
      {
        role: 'system',
        content: '你是意图识别助手，只输出 JSON 格式: {"intent": "...", "confidence": 0-1}',
      },
      { role: 'user', content: message },
    ],
    temperature: 0.2,
  };

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'api-key': apiKey,
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    return NextResponse.json({ intent: 'error', confidence: 0, raw: detail }, { status: 500 });
  }

  const data = (await response.json()) as {
    choices?: { message?: { content?: string } }[];
  };
  const content = data.choices?.[0]?.message?.content ?? '';

  try {
    const parsed = JSON.parse(content);
    return NextResponse.json({
      intent: parsed.intent ?? '',
      confidence: parsed.confidence ?? 0.6,
      raw: content,
    });
  } catch {
    return NextResponse.json({ intent: content.trim(), confidence: 0.5, raw: content });
  }
}
