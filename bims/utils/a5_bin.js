'use strict';
// Reads JSON from stdin: { points: [[lon, lat], ...], resolution: N }
// Writes JSON to stdout: [{ count: N, boundary: [[lon, lat], ...] }, ...]
// BigInt cell IDs are handled internally; only plain JSON crosses the boundary.
const { lonLatToCell, cellToBoundary } = require('a5-js');

const chunks = [];
process.stdin.on('data', chunk => chunks.push(chunk));
process.stdin.on('end', () => {
    try {
        const { points, resolution } = JSON.parse(Buffer.concat(chunks).toString());
        const counts = new Map();
        for (const [lon, lat] of points) {
            const cell = lonLatToCell([lon, lat], resolution);
            const key = cell.toString();
            counts.set(key, (counts.get(key) ?? 0) + 1);
        }
        const result = [];
        for (const [key, count] of counts) {
            // closedRing defaults to true, so boundary[0] === boundary[-1].
            result.push({ count, boundary: cellToBoundary(BigInt(key)) });
        }
        process.stdout.write(JSON.stringify(result));
    } catch (err) {
        process.stderr.write(err.message + '\n');
        process.exit(1);
    }
});
