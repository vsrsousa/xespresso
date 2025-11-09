"""
Calculation preparation module for xespresso GUI.

This module handles the creation of Espresso calculator and atoms objects
from GUI configuration, following xespresso's design patterns.
"""

from typing import Dict, Tuple, Optional
from ase import Atoms
from xespresso import Espresso
from xespresso.gui.calculations.base import BaseCalculationPreparation
import logging

logger = logging.getLogger(__name__)


class CalculationPreparation(BaseCalculationPreparation):
    """
    Prepares calculations (SCF, relax, vc-relax) from GUI configuration.
    
    This class encapsulates the logic for creating Espresso calculator
    objects from GUI workflow_config dictionary, ensuring that calculator
    creation happens in a dedicated module rather than in main GUI code
    or job submission code.
    
    Examples:
        >>> # In GUI calculation setup or workflow builder:
        >>> prep = CalculationPreparation(atoms, config, label='scf/fe')
        >>> atoms, calc = prep.prepare()
        >>> 
        >>> # In GUI job submission:
        >>> # Just receive the prepared objects and execute
        >>> calc.run(atoms=atoms)
    """
    
    def prepare(self) -> Tuple[Atoms, Espresso]:
        """
        Prepare atoms and Espresso calculator from GUI configuration.
        
        This method creates the Espresso calculator with parameters from
        the GUI's workflow_config dictionary, following xespresso patterns.
        
        Returns:
            tuple: (atoms, calculator) ready for execution or dry run
        """
        config = self.config
        
        # Validate required configuration
        if 'pseudopotentials' not in config or not config['pseudopotentials']:
            raise ValueError("Configuration must include pseudopotentials")
        
        # Build calculator parameters from GUI configuration
        calc_params = {
            'pseudopotentials': config['pseudopotentials'],
            'label': self.label,
        }
        
        # Build input_data dictionary following xespresso patterns
        input_data = {}
        
        # Add basic parameters
        if 'ecutwfc' in config:
            input_data['ecutwfc'] = config['ecutwfc']
        if 'ecutrho' in config:
            input_data['ecutrho'] = config['ecutrho']
        if 'occupations' in config:
            input_data['occupations'] = config['occupations']
        if 'conv_thr' in config:
            input_data['conv_thr'] = config['conv_thr']
        
        # Add smearing parameters if using smearing occupation
        if config.get('occupations') == 'smearing':
            input_data['smearing'] = config.get('smearing', 'gaussian')
            input_data['degauss'] = config.get('degauss', 0.02)
        
        # Add spin polarization
        if 'nspin' in config:
            input_data['nspin'] = config['nspin']
        
        # Add magnetic moments if present
        if 'starting_magnetization' in config:
            input_data['starting_magnetization'] = config['starting_magnetization']
        
        # Add calculation type
        calc_type = config.get('calc_type', 'scf')
        if calc_type in ['relax', 'vc-relax']:
            input_data['calculation'] = calc_type
            # Add relaxation-specific parameters
            if 'forc_conv_thr' in config:
                input_data['forc_conv_thr'] = config['forc_conv_thr']
        else:
            input_data['calculation'] = 'scf'
        
        # Add DFT+U parameters if present
        if 'lda_plus_u' in config:
            input_data['lda_plus_u'] = config['lda_plus_u']
        if 'Hubbard_U' in config:
            input_data['Hubbard_U'] = config['Hubbard_U']
        
        calc_params['input_data'] = input_data
        
        # Add k-points from config
        if 'kspacing' in config:
            calc_params['kspacing'] = config['kspacing']
        elif 'kpts' in config:
            calc_params['kpts'] = config['kpts']
        else:
            # Default to gamma point
            calc_params['kpts'] = (1, 1, 1)
        
        # Add queue configuration if present (for job submission)
        if 'queue' in config and config['queue']:
            calc_params['queue'] = config['queue']
        
        # Add parallel execution parameters if present
        if 'parallel' in config and config['parallel']:
            calc_params['parallel'] = config['parallel']
        
        # Add any additional parameters from config
        for key in ['package', 'debug']:
            if key in config:
                calc_params[key] = config[key]
        
        # Create Espresso calculator using xespresso
        logger.info(f"Creating Espresso calculator with label={self.label}")
        self.calculator = Espresso(**calc_params)
        
        logger.info(f"Successfully prepared {calc_type} calculation")
        
        return self.atoms, self.calculator


def prepare_calculation_from_gui(
    atoms: Atoms,
    config: Dict,
    label: str = "calculation"
) -> Tuple[Atoms, Espresso]:
    """
    Convenience function to prepare calculation from GUI configuration.
    
    This function encapsulates the calculator preparation logic,
    ensuring that atoms and Espresso objects are created in the
    calculation module rather than in main GUI or job submission code.
    
    Args:
        atoms: ASE Atoms object
        config: GUI workflow configuration dictionary
        label: Calculation label/directory
        
    Returns:
        tuple: (atoms, calculator) ready for execution
        
    Example:
        >>> # In GUI pages (calculation_setup, workflow_builder):
        >>> atoms, calc = prepare_calculation_from_gui(
        ...     st.session_state.current_structure,
        ...     st.session_state.workflow_config,
        ...     label='scf/fe'
        ... )
        >>> st.session_state.espresso_calculator = calc
        >>> st.session_state.prepared_atoms = atoms
    """
    prep = CalculationPreparation(atoms, config, label)
    return prep.prepare()


def dry_run_calculation(
    atoms: Atoms,
    config: Dict,
    label: str = "calculation"
) -> Tuple[Atoms, Espresso]:
    """
    Prepare calculation and generate input files (dry run).
    
    This function creates the calculator and writes input files
    without executing the calculation. Useful for reviewing
    parameters before submission.
    
    Args:
        atoms: ASE Atoms object
        config: GUI workflow configuration dictionary
        label: Calculation label/directory
        
    Returns:
        tuple: (atoms, calculator) with input files written
        
    Example:
        >>> # In GUI dry run tab:
        >>> atoms, calc = dry_run_calculation(
        ...     st.session_state.current_structure,
        ...     st.session_state.workflow_config,
        ...     label='scf/fe'
        ... )
        >>> st.success(f"Input files written to {calc.directory}")
    """
    atoms, calc = prepare_calculation_from_gui(atoms, config, label)
    
    # Write input files using xespresso's method
    calc.write_input(atoms)
    
    logger.info(f"Dry run complete - input files written to {calc.directory}")
    
    return atoms, calc
