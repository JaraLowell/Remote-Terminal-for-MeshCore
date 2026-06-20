export const SPAM_PACKET_CATEGORY_LABELS: Record<string, string> = {
  pm_transport: 'PM Transport',
  dm: 'Direct DM',
  group_transport: 'Group Text Transport',
  group_text: 'Group Text',
  request: 'Request',
  response: 'Response',
  path: 'Path',
  ack: 'ACK',
  advert: 'Advert',
  anon_request: 'Anon Request',
  trace: 'Trace',
  control: 'Control',
  other: 'Other',
};

export function spamCategoryLabel(
  category: string | null | undefined,
  labels?: Record<string, string>,
): string {
  if (!category) return 'Mixed';
  return labels?.[category] ?? SPAM_PACKET_CATEGORY_LABELS[category] ?? category;
}

export function formatSpamCategoryBreakdown(
  counts: Record<string, number> | undefined,
  labels?: Record<string, string>,
  total?: number,
): string {
  if (!counts || Object.keys(counts).length === 0) {
    return 'Unknown';
  }

  const packetTotal = total ?? Object.values(counts).reduce((sum, value) => sum + value, 0);
  if (packetTotal <= 0) {
    return spamCategoryLabel(Object.keys(counts)[0], labels);
  }

  const parts = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([category, count]) => {
      const share = Math.round((count / packetTotal) * 100);
      return `${spamCategoryLabel(category, labels)} (${share}%)`;
    });

  return parts.join(', ');
}
