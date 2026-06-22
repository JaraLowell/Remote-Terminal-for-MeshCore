/**
 * Canonical packet-type colors used across map live traffic, raw packet feed,
 * spam defense charts, and the 3D packet visualizer.
 */

export const PACKET_TYPE_COLOR_HEX = {
  Request: '#9333ea',
  Response: '#7dd3fc',
  Control: '#0077b6',
  Path: '#10b981',
  Advert: '#84cc16',
  AnonRequest: '#ef4444',
  Ack: '#6366f1',
  TextMessage: '#f97316',
  GroupText: '#ec4899',
  Trace: '#f59e0b',
  GroupData: '#c084fc',
  Atlas: '#64748b',
  Location: '#22d3ee',
  Tracker: '#22c55e',
  Unknown: '#6b7280',
} as const;

export type PacketTypeColorName = keyof typeof PACKET_TYPE_COLOR_HEX;

/** Spam live/historical timeline categories (backend `classify_packet_header`). */
export const SPAM_CATEGORY_COLOR_HEX: Record<string, string> = {
  request: PACKET_TYPE_COLOR_HEX.Request,
  response: PACKET_TYPE_COLOR_HEX.Response,
  control: PACKET_TYPE_COLOR_HEX.Control,
  path: PACKET_TYPE_COLOR_HEX.Path,
  advert: PACKET_TYPE_COLOR_HEX.Advert,
  anon_request: PACKET_TYPE_COLOR_HEX.AnonRequest,
  ack: PACKET_TYPE_COLOR_HEX.Ack,
  dm: PACKET_TYPE_COLOR_HEX.TextMessage,
  pm_transport: '#fb923c',
  group_transport: '#f472b6',
  group_text: PACKET_TYPE_COLOR_HEX.GroupText,
  trace: PACKET_TYPE_COLOR_HEX.Trace,
  other: PACKET_TYPE_COLOR_HEX.Unknown,
};

/** Short labels used by the visualizer and map particle animation. */
export type PacketVisualizerLabel =
  | 'AD'
  | 'GT'
  | 'DM'
  | 'AK'
  | 'PA'
  | 'TR'
  | 'RQ'
  | 'AR'
  | 'RS'
  | 'CT'
  | '?';

const VISUALIZER_LABEL_COLORS: Record<PacketVisualizerLabel, string> = {
  AD: PACKET_TYPE_COLOR_HEX.Advert,
  GT: PACKET_TYPE_COLOR_HEX.GroupText,
  DM: PACKET_TYPE_COLOR_HEX.TextMessage,
  AK: PACKET_TYPE_COLOR_HEX.Ack,
  PA: PACKET_TYPE_COLOR_HEX.Path,
  TR: PACKET_TYPE_COLOR_HEX.Trace,
  RQ: PACKET_TYPE_COLOR_HEX.Request,
  AR: PACKET_TYPE_COLOR_HEX.AnonRequest,
  RS: PACKET_TYPE_COLOR_HEX.Response,
  CT: PACKET_TYPE_COLOR_HEX.Control,
  '?': PACKET_TYPE_COLOR_HEX.Unknown,
};

export function getVisualizerLabelColor(label: PacketVisualizerLabel): string {
  return VISUALIZER_LABEL_COLORS[label];
}

export const VISUALIZER_LABEL_COLORS_MAP: Readonly<Record<PacketVisualizerLabel, string>> =
  VISUALIZER_LABEL_COLORS;

const BACKEND_PAYLOAD_TYPE_ALIASES: Record<string, PacketTypeColorName> = {
  ADVERT: 'Advert',
  GROUPTEXT: 'GroupText',
  TEXTMESSAGE: 'TextMessage',
  PRIV: 'TextMessage',
  CHAN: 'GroupText',
  ACK: 'Ack',
  PATH: 'Path',
  REQUEST: 'Request',
  RESPONSE: 'Response',
  ANONREQUEST: 'AnonRequest',
  ANON_REQUEST: 'AnonRequest',
  CONTROL: 'Control',
  COMMAND: 'Control',
  TRACE: 'Trace',
  GROUPDATA: 'GroupData',
  ATLAS: 'Atlas',
  LOCATION: 'Location',
  TRACKER: 'Tracker',
  UNKNOWN: 'Unknown',
};

export function getPayloadTypeNameColor(name: string | null | undefined): string {
  if (!name) return PACKET_TYPE_COLOR_HEX.Unknown;
  const trimmed = name.trim();
  if (!trimmed) return PACKET_TYPE_COLOR_HEX.Unknown;

  if (trimmed in PACKET_TYPE_COLOR_HEX) {
    return PACKET_TYPE_COLOR_HEX[trimmed as PacketTypeColorName];
  }

  const alias = BACKEND_PAYLOAD_TYPE_ALIASES[trimmed.toUpperCase()];
  if (alias) return PACKET_TYPE_COLOR_HEX[alias];

  const upper = trimmed.toUpperCase();
  if (upper.includes('ANON') && upper.includes('REQUEST')) {
    return PACKET_TYPE_COLOR_HEX.AnonRequest;
  }
  if (upper.includes('ADVERT')) return PACKET_TYPE_COLOR_HEX.Advert;
  if (upper === 'PATH') return PACKET_TYPE_COLOR_HEX.Path;
  if (upper.includes('ACK')) return PACKET_TYPE_COLOR_HEX.Ack;
  if (upper.includes('RESPONSE')) return PACKET_TYPE_COLOR_HEX.Response;
  if (upper.includes('REQUEST')) return PACKET_TYPE_COLOR_HEX.Request;
  if (upper.includes('CONTROL') || upper.includes('COMMAND')) {
    return PACKET_TYPE_COLOR_HEX.Control;
  }
  if (upper.includes('GROUP')) return PACKET_TYPE_COLOR_HEX.GroupText;
  if (upper.includes('TEXT')) return PACKET_TYPE_COLOR_HEX.TextMessage;
  if (upper.includes('TRACE')) return PACKET_TYPE_COLOR_HEX.Trace;
  return PACKET_TYPE_COLOR_HEX.Unknown;
}

export function getSpamCategoryColor(category: string | null | undefined): string {
  if (!category) return SPAM_CATEGORY_COLOR_HEX.other;
  return SPAM_CATEGORY_COLOR_HEX[category] ?? SPAM_CATEGORY_COLOR_HEX.other;
}

export const PACKET_VISUALIZER_LEGEND_ITEMS = [
  { label: 'AD', color: VISUALIZER_LABEL_COLORS.AD, description: 'Advertisement' },
  { label: 'GT', color: VISUALIZER_LABEL_COLORS.GT, description: 'Group Text' },
  { label: 'DM', color: VISUALIZER_LABEL_COLORS.DM, description: 'Direct Message' },
  { label: 'RQ', color: VISUALIZER_LABEL_COLORS.RQ, description: 'Request' },
  { label: 'RS', color: VISUALIZER_LABEL_COLORS.RS, description: 'Response' },
  { label: 'AR', color: VISUALIZER_LABEL_COLORS.AR, description: 'Anon Request' },
  { label: 'PA', color: VISUALIZER_LABEL_COLORS.PA, description: 'Path' },
  { label: 'AK', color: VISUALIZER_LABEL_COLORS.AK, description: 'Acknowledgment' },
  { label: 'CT', color: VISUALIZER_LABEL_COLORS.CT, description: 'Control' },
  { label: 'TR', color: VISUALIZER_LABEL_COLORS.TR, description: 'Trace' },
  { label: '?', color: VISUALIZER_LABEL_COLORS['?'], description: 'Other' },
] as const;
