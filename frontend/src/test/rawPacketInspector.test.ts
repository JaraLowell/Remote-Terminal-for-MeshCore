import { describe, expect, it } from 'vitest';
import { PayloadType } from '@michaelhart/meshcore-decoder';

import {
  buildRawPacketRoutedSummary,
  describeCiphertextStructure,
  formatFeedHashToken,
  formatHexByHop,
} from '../utils/rawPacketInspector';

describe('rawPacketInspector helpers', () => {
  it('caps hex feed tokens at six characters', () => {
    expect(formatFeedHashToken('78368a1e9abc')).toBe('78368A');
    expect(formatFeedHashToken('7a')).toBe('7A');
    expect(formatFeedHashToken('MountainTop')).toBe('MountainTop');
  });

  it('builds routed summaries with from/for and path suffix', () => {
    expect(
      buildRawPacketRoutedSummary('AnonRequest', {
        source: '78368a1e9abc',
        destination: '7a',
        pathStr: ' via 5FF7, 1876',
      })
    ).toBe('AnonRequest from 78368A for 7A via 5FF7, 1876');
    expect(
      buildRawPacketRoutedSummary('DM', {
        source: 'aa',
        destination: 'bb',
        pathStr: '',
        destinationWord: 'to',
      })
    ).toBe('DM from AA to BB');
    expect(
      buildRawPacketRoutedSummary('Response', {
        destination: '34',
        pathStr: ' via AB',
      })
    ).toBe('Response for 34 via AB');
  });

  it('formats path hex as hop-delimited groups', () => {
    expect(formatHexByHop('A1B2C3D4E5F6', 2)).toBe('A1B2 → C3D4 → E5F6');
    expect(formatHexByHop('AABBCC', 1)).toBe('AA → BB → CC');
  });

  it('leaves non-hop-aligned hex unchanged', () => {
    expect(formatHexByHop('A1B2C3', 2)).toBe('A1B2C3');
    expect(formatHexByHop('A1B2', null)).toBe('A1B2');
  });

  it('describes undecryptable ciphertext with multiline bullets', () => {
    expect(describeCiphertextStructure(PayloadType.GroupText, 9, 'fallback')).toContain(
      '\n• Timestamp (4 bytes)'
    );
    expect(describeCiphertextStructure(PayloadType.GroupText, 9, 'fallback')).toContain(
      '\n• Flags (1 byte)'
    );
    expect(describeCiphertextStructure(PayloadType.TextMessage, 12, 'fallback')).toContain(
      '\n• Message (remaining bytes)'
    );
  });
});
