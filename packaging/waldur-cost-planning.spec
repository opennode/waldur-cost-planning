Name: waldur-cost-planning
Summary: Waldur cost planning plugin
Group: Development/Libraries
Version: 0.4.2
Release: 1.el7
License: MIT
Url: http://waldur.com
Source0: %{name}-%{version}.tar.gz

Requires: waldur-core >= 0.142.0
Requires: waldur-openstack >= 0.30.2
Requires: waldur-digitalocean >= 0.8.2
Requires: waldur-aws >= 0.9.2

Obsoletes: nodeconductor-cost-planning

BuildArch: noarch
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot

BuildRequires: python-setuptools

%description
Waldur cost planning plugin allows to get a price estimate without actually creating the infrastructure.

%prep
%setup -q -n %{name}-%{version}

%build
%{__python} setup.py build

%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --root=%{buildroot}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%{python_sitelib}/*

%changelog
* Mon Jul 3 2017 Jenkins <jenkins@opennodecloud.com> - 0.4.2-1.el7
- New upstream release
