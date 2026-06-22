import { describe, expect, it } from 'vitest';

import {
  getPayloadTypeNameColor,
  getSpamCategoryColor,
  getVisualizerLabelColor,
  PACKET_TYPE_COLOR_HEX,
} from '../utils/packetTypeColors';

describe('packetTypeColors', () => {
  it('uses the canonical palette for primary packet types', () => {
    expect(getPayloadTypeNameColor('Request')).toBe(PACKET_TYPE_COLOR_HEX.Request);
    expect(getPayloadTypeNameColor('Response')).toBe(PACKET_TYPE_COLOR_HEX.Response);
    expect(getPayloadTypeNameColor('Control')).toBe(PACKET_TYPE_COLOR_HEX.Control);
    expect(getPayloadTypeNameColor('Path')).toBe(PACKET_TYPE_COLOR_HEX.Path);
    expect(getPayloadTypeNameColor('Advert')).toBe(PACKET_TYPE_COLOR_HEX.Advert);
    expect(getPayloadTypeNameColor('AnonRequest')).toBe(PACKET_TYPE_COLOR_HEX.AnonRequest);
  });

  it('maps backend aliases consistently', () => {
    expect(getPayloadTypeNameColor('ADVERT')).toBe(PACKET_TYPE_COLOR_HEX.Advert);
    expect(getPayloadTypeNameColor('PATH')).toBe(PACKET_TYPE_COLOR_HEX.Path);
    expect(getPayloadTypeNameColor('ACK')).toBe(PACKET_TYPE_COLOR_HEX.Ack);
    expect(getPayloadTypeNameColor('ANON_REQUEST')).toBe(PACKET_TYPE_COLOR_HEX.AnonRequest);
  });

  it('aligns spam categories with packet colors', () => {
    expect(getSpamCategoryColor('request')).toBe(PACKET_TYPE_COLOR_HEX.Request);
    expect(getSpamCategoryColor('response')).toBe(PACKET_TYPE_COLOR_HEX.Response);
    expect(getSpamCategoryColor('control')).toBe(PACKET_TYPE_COLOR_HEX.Control);
    expect(getSpamCategoryColor('path')).toBe(PACKET_TYPE_COLOR_HEX.Path);
    expect(getSpamCategoryColor('advert')).toBe(PACKET_TYPE_COLOR_HEX.Advert);
    expect(getSpamCategoryColor('anon_request')).toBe(PACKET_TYPE_COLOR_HEX.AnonRequest);
  });

  it('exposes visualizer label colors from the same palette', () => {
    expect(getVisualizerLabelColor('RQ')).toBe(PACKET_TYPE_COLOR_HEX.Request);
    expect(getVisualizerLabelColor('RS')).toBe(PACKET_TYPE_COLOR_HEX.Response);
    expect(getVisualizerLabelColor('CT')).toBe(PACKET_TYPE_COLOR_HEX.Control);
    expect(getVisualizerLabelColor('PA')).toBe(PACKET_TYPE_COLOR_HEX.Path);
    expect(getVisualizerLabelColor('AD')).toBe(PACKET_TYPE_COLOR_HEX.Advert);
    expect(getVisualizerLabelColor('AR')).toBe(PACKET_TYPE_COLOR_HEX.AnonRequest);
  });
});
