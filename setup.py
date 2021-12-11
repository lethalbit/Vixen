# SPDX-License-Identifier: BSD-3-Clause

from setuptools import setup, find_packages

def vcs_ver():
	def scheme(version):
		if version.tag and not version.distance:
			return version.format_with("")
		else:
			return version.format_choice("+{node}", "+{node}.dirty")
	return {
		"relative_to": __file__,
		"version_scheme": "guess-next-dev",
		"local_scheme": scheme
	}

def doc_ver():
	try:
		from setuptools_scm.git import parse as parse_git
	except ImportError:
		return ""

	git = parse_git(".")
	if not git:
		return ""
	elif git.exact:
		return git.format_with("{tag}")
	else:
		return "latest"

setup(
	name = 'Vixen',
	use_scm_version = vcs_ver(),
	author          = 'Aki \'lethalbit\' Van Ness',
	author_email    = 'nya@catgirl.link',
	description     = 'VAX soft-core and SoC',
	license         = 'BSD-3-Clause',
	python_requires = '>=3.8,<3.10',
	zip_safe        = False,

	setup_requires  = [
		'wheel',
		'setuptools',
		'setuptools_scm'
	],

	install_requires = [
		'Jinja2',

		'amaranth @ git+https://github.com/amaranth-lang/amaranth.git@master',
		'amaranth-boards @ git+https://github.com/amaranth-lang/amaranth-soc.git@master',
		'amaranth-stdio @ git+https://github.com/amaranth-lang/amaranth-stdio.git@master',
	],

	packages = find_packages(),

	entry_points = {
		'console_scripts': [
			'Vixen = vixen:main',
		],
	},

	classifiers = [
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: BSD License',

		'Intended Audience :: Developers',
		'Intended Audience :: Information Technology',
		'Intended Audience :: System Administrators',

		'Topic :: Software Development',
		'Topic :: System :: Hardware',

	],

	project_urls = {
		'Documentation': 'https://github.com/lethalbit/Vixen',
		'Source Code'  : 'https://github.com/lethalbit/Vixen',
		'Bug Tracker'  : 'https://github.com/lethalbit/Vixen/issues',
	}
)
