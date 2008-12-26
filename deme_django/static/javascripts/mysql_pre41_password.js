// ported to javascript from http://packages.debian.org/lenny/libcrypt-mysql-perl
function mysql_pre41_password(raw_password) {

    function zero_pad(str, length) {
        while (str.length < length) str = '0' + str;
        return str;
    }

    function number_to_bin_string(x) {
        // stored LSB on left
        var result = '';
        while (x > 0) {
            result = result + (x % 2 == 1 ? '1' : '0');
            x = Math.floor(x / 2);
        }
        return result;
    }

    function bin_string_to_32bit_number(x) {
        var result = 0;
        for (var i = 0; i < Math.min(31, x.length); i++) {
            if (x[i] == '1') result += 1 << i;
        }
        return result;
    }

    function bin_string_to_hex_string(x) {
        var result = '';
        for (var i = 0; i < x.length; i += 4) {
            var h = 0;
            for (var j = i; j < Math.min(i + 4, x.length); j++) {
                h = h + ((x[j] == '1' ? 1 : 0) << (j - i));
            }
            result = h.toString(16) + result;
        }
        return result;
    }

    function bin_and(x, y) {
        if (x.length < y.length) {
            var tmp = x;
            x = y;
            y = tmp;
        }
        // x has more length
        var result = '';
        for (var i = 0; i < y.length; i++) {
            var xbit = parseInt(x[i], 10);
            var ybit = parseInt(y[i], 10);
            result = result + (xbit & ybit == 1 ? '1' : '0');
        }
        return result;
    }

    function bin_xor(x, y) {
        if (x.length < y.length) {
            var tmp = x;
            x = y;
            y = tmp;
        }
        // x has more length
        var result = '';
        for (var i = 0; i < x.length; i++) {
            var xbit = parseInt(x[i], 10);
            var ybit = (i >= y.length ? 0 : parseInt(y[i], 10));
            result = result + (xbit ^ ybit == 1 ? '1' : '0');
        }
        return result;
    }

    function bin_plus(x, y) {
        if (x.length < y.length) {
            var tmp = x;
            x = y;
            y = tmp;
        }
        // x has more length
        var result = '';
        var carry = 0;
        for (var i = 0; i < x.length; i++) {
            var xbit = parseInt(x[i], 10);
            var ybit = (i >= y.length ? 0 : parseInt(y[i], 10));
            var sum = carry + xbit + ybit;
            result = result + (sum % 2 == 1 ? '1' : '0');
            carry = (sum >= 2 ? 1 : 0);
        }
        if (carry) result = result + '1';
        return result;
    }

    function bin_times(x, y) {
        var result = '';
        var z = '0';
        for (var i = 0; i < 2 * Math.max(x.length, y.length); i++) {
            for (var j = 0; j <= i; j++) {
                var k = i - j;
                if (x[j] == '1' && y[k] == '1') {
                    z = bin_plus(z, '1');
                }
            }
            result = result + z[0];
            z = z.substring(1);
            if (z.length == 0) z = '0';
        }
        return result;
    }

    function bin_lshift(x, bits) {
        for (var i = 0; i < bits; i++) {
            x = '0' + x;
        }
        return x;
    }

    function encrypt() {
        var nr = number_to_bin_string(1345345333);
        var add = number_to_bin_string(7);
        var nr2 = number_to_bin_string(0x12345671);
        for (var i = 0; i < raw_password.length; i++) {
            var ch = raw_password[i];
            if (ch == ' ' || ch == '\t') {
                continue; // skip spaces in raw_password
            }
            var tmp = number_to_bin_string(raw_password.charCodeAt(i));
            nr = bin_xor(nr, bin_plus(bin_times(bin_plus(bin_and(nr, number_to_bin_string(63)), add), tmp), bin_lshift(nr, 8)));
            nr2 = bin_plus(nr2, bin_xor(bin_lshift(nr2, 8), nr));
            add = bin_plus(add, tmp);
        }
        var result1 = bin_string_to_32bit_number(nr);
        var result2 = bin_string_to_32bit_number(nr2);
        return zero_pad(result1.toString(16), 8) + zero_pad(result2.toString(16), 8);
    }

    return encrypt();
}

