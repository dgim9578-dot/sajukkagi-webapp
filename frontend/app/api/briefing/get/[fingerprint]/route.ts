import { NextRequest } from "next/server";

import { getLocalSampleBriefing } from "@/lib/demo-briefing";
import { loadBriefingFromLocalProject } from "@/lib/briefing-load-local";
import { get_briefing_by_fingerprint } from "@/lib/storage";

export async function GET(
  _request: NextRequest,
  { params }: { params: { fingerprint: string } }
) {
  const fingerprint = params.fingerprint?.trim();
  if (!fingerprint) {
    return Response.json({ error: "fingerprint가 비어 있습니다." }, { status: 400 });
  }

  try {
    if (fingerprint === "test_sample_123") {
      return Response.json({
        success: true,
        briefing: getLocalSampleBriefing(),
      });
    }

    let briefing: Awaited<ReturnType<typeof get_briefing_by_fingerprint>> = null;
    try {
      briefing = await get_briefing_by_fingerprint(fingerprint);
    } catch {
      briefing = null;
    }
    if (!briefing) {
      briefing = await loadBriefingFromLocalProject(fingerprint);
    }

    if (!briefing) {
      return Response.json(
        {
          error:
            "브리핑을 찾을 수 없습니다. STEP2에서 저장한 뒤 STEP3을 다시 열어 주세요.",
        },
        { status: 404 }
      );
    }

    return Response.json({ success: true, briefing });
  } catch (e) {
    const message =
      e instanceof Error ? e.message : "브리핑을 불러오지 못했습니다.";
    return Response.json({ error: message }, { status: 502 });
  }
}
