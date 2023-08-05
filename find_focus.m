center_roi = 0.5;
n_interp = 1; % How many points to use for parabolic interpolation?

stackdir = 'zstack';

vf = dir(stackdir);
vmask = false(numel(vf),1);
for idxf=1:numel(vf) % Find .jpgs
    if(strcmp('.jpg', vf(idxf).name(max(1,(end-3)):end))), vmask(idxf) = true; end
end
vf = vf(vmask);
nf = numel(vf);

% Set up dimensions;
str_name = sprintf('%s/%s', stackdir, vf(1).name);
img = imread(str_name);
sz = size(img);
c_roi = { ...
    [floor(sz(1)*(1-center_roi)/2), ceil(sz(1)*(1+center_roi)/2)], ... % Rows
    [floor(sz(2)*(1-center_roi)/2), ceil(sz(2)*(1+center_roi)/2)], ... % Cols
    };

% Build focus stack metric
vz = nan(nf,1);
vad2 = nan(nf,1);
for idxf=1:nf
    str_name = sprintf('%s/%s', stackdir, vf(idxf).name);
    img = imread(str_name, ...
        'PixelRegion', c_roi);
    img = sum(img, 3);
    img = abs(diff(img, 2)).^2;
    vad2(idxf) = sum(img(:));
    vz(idxf) = str2num(vf(idxf).name(2:(end-4))); % 'z##.##.jpg'
end

% Select points for parabolic peak interpolation
[pmax, idxpeak] = max(vad2);
zmax = vz(idxpeak);
idxc = max(min(idxpeak,nf-n_interp),n_interp+1); % Center of parabolic interpolation
vpidx = (idxc-n_interp):(idxc+n_interp);
vp = vad2(vpidx);
vpz = vz(vpidx);

% Remove centers
cpz = mean(vpz);
cp = vp(ceil(numel(vpidx)/2));
vpz = vpz-cpz;
vp = vp-cp;

vp_coeff = [vpz, vpz.^2]\vp; % Fit a parabola
if(vp_coeff(2) < 0) % If false, don't interpolate: the parabola is bad.
  zmax = -vp_coeff(1)/(2*vp_coeff(2));
  pmax = cp + vp_coeff(1)*zmax + vp_coeff(2)*zmax^2;
  zmax = zmax + cpz;
end

% Plotting
vpz_plot = linspace(min(vpz), max(vpz), 100);
vp_plot = cp + vp_coeff(1)*vpz_plot + vp_coeff(2)*vpz_plot.^2;
vpz_plot = vpz_plot + cpz;

hold on;
plot(vz, vad2, ...
    'DisplayName', 'Focus metric', ...
    'LineWidth', 2);
plot(vpz_plot, vp_plot, ...
    'DisplayName', 'Focus metric (interp.)', ...
    'LineWidth', 2);
scatter(zmax, pmax, 40, 'filled', ...
  'DisplayName', 'Best focus');
grid on;
legend
xlabel('z')

