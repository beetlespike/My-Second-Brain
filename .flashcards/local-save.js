async function saveToVault(payload, onConflict) {
  const response = await fetch('feedback', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  });
  const receipt = await response.json();
  if (!response.ok) {
    const error = new Error(receipt.error || '知识库未能保存反馈。');
    error.status = response.status;
    error.receipt = receipt;
    if (response.status === 409 && receipt.card_id && typeof onConflict === 'function') {
      onConflict(receipt);
    }
    throw error;
  }
  if (!Number.isInteger(receipt.saved) || !Number.isInteger(receipt.duplicates) ||
      !Number.isInteger(receipt.historical_only) || receipt.saved + receipt.duplicates !== payload.entries.length) {
    throw new Error('尚未收到完整的保存回执。');
  }
  if (payload.entries.some(entry => 'expected_rating_sequence' in entry)) {
    for (const entry of payload.entries) {
      if (entry.card_id.startsWith('study:')) continue;
      const state = receipt.rating_states?.[entry.card_id];
      if (!state || !(state.rating_lock === null || typeof state.rating_lock?.code === 'string') ||
          !(state.saved_rating === null && state.rating_sequence === null ||
            ['again', 'uncertain', 'familiar'].includes(state.saved_rating) &&
            Number.isSafeInteger(state.rating_sequence) && state.rating_sequence >= 1)) {
        throw new Error('尚未收到完整的评分回执。');
      }
    }
  }
  return receipt;
}
