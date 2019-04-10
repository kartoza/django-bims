define(['backbone', 'utils/class'], function (Backbone, UtilClass) {
    var ColorUtil = UtilClass.extend({
        initialize: function () {
        },
        hslToRgb: function (h, s, l) {
            let r, g, b;
            const rd = (a) => {
                return Math.floor(Math.max(Math.min(a * 256, 255), 0));
            };
            const hueToRGB = (m, n, o) => {
                if (o < 0) o += 1;
                if (o > 1) o -= 1;
                if (o < 1 / 6) return m + (n - m) * 6 * o;
                if (o < 1 / 2) return n;
                if (o < 2 / 3) return m + (n - m) * (2 / 3 - o) * 6;
                return m;
            };
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hueToRGB(p, q, h + 1 / 3);
            g = hueToRGB(p, q, h);
            b = hueToRGB(p, q, h - 1 / 3);
            return [rd(r), rd(g), rd(b)]
        },
        rgbToHex: function (r, g, b) {
            return `#${r.toString(16)}${g.toString(16)}${b.toString(16)}`;
        },
        generateHexColor: function () {
            const hBase = Math.random();
            const newL = Math.floor(Math.random() * 16) + 75;
            const [ r, g, b ] = this.hslToRgb(hBase, 1, newL*.01);
            return `${this.rgbToHex(r,g,b)}`
        }
    });
    return ColorUtil;
});