// Both API records and static exports use the same five independent signal groups.
// Boolean fields are authoritative; scores, durations and card colors are not flags.
(function (root) {
    function isTrue(value) {
        return value === true || value === 1 || value === 'True' || value === 'true';
    }
    function normalize(record) {
        const nested = record.flags || {};
        const value = (key, alias = key) => record[key] ?? nested[key] ?? nested[alias];
        return {
            flag_delay: isTrue(value('flag_delay')),
            flag_amount: isTrue(value('flag_amount')),
            flag_mp_drift: isTrue(value('flag_mp_drift')),
            flag_isolation_forest: isTrue(value('flag_isolation_forest', 'iso_flag')),
            dq_flag: ['dq_flag', 'dq_implausible_amount', 'dq_possible_miscategorization', 'dq_stale_status']
                .some(key => isTrue(value(key))),
        };
    }
    function count(record) {
        return Object.values(normalize(record)).filter(Boolean).length;
    }
    root.DossierSignals = {normalize, count, isTrue};
    if (typeof module !== 'undefined') module.exports = root.DossierSignals;
})(typeof window !== 'undefined' ? window : globalThis);
