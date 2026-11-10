import decimal as deci
from functools import partial
import maya.cmds as cmds #type: ignore
import maya.mel as mel #type: ignore

# Local MotionTrail
# Maya 2024-2026+ | 1.0.0
# Julien Rogar ( https://github.com/JulienRogar/Local-MotionTrail )


# --- Variables ---
global_win_instances = []
global_win_count = 0
# --- Variables ---

class Local_MotionTrail_Window():
    def __init__( self, multi_windows=True, keep_win_pref=False, expanded=True ):
        """
        Local_MotionTrail\n
        ### Parameters:\n
        'multi_windows' (bool): Create a new window instance of the tool\n
        'keep_win_pref' (bool): Keep window preferences as position or size\n
          Note: If multiple windows, each one will have it's own window preferences saved following their incremented name\n
        'expanded' (bool): Build expanded or contracted window by default
        """
        # --- Variables ---
        self.WINDOW = None
        self.SELF_IDX = _Get_WindowIdx( self, multi_windows )
        SELF_IDX = self.SELF_IDX
        self.WIN_NAME = f"Local_MotionTrail_{SELF_IDX}"
        self.WIN_TITLE = f"Local MotionTrail - 1.0.0 - [Maya 2024+]"
        self.WIN_SIZE_SETS = ( (810,423), (260,280) )
        self.WIN_SIZE_WH = self.WIN_SIZE_SETS[0] if expanded else self.WIN_SIZE_SETS[1]
        self.WIN_SIZEABLE = True
        self.WIN_KEEP_PREF = keep_win_pref

        self.THEME = {
            'main_back':(0.26, 0.26, 0.26),
            'sys_pick_back_off':(0.2, 0.2, 0.2),
            'sys_pick_back_on':(0.13, 0.13, 0.13),
            'sys_pickField_back':(0.2, 0.2, 0.2),
            'sys_bttn_back':(0.2, 0.2, 0.2),
            'sys_symbolChckBx_high_back':(0.13, 0.13, 0.13),
            'sys_deleteBttn_back':(0.2, 0.07, 0.07),
            'pick_back_off':(0.17, 0.17, 0.17),
            'pick_back_on':(0.33, 0.33, 0.33),
            'pickField_back':(0.15, 0.15, 0.15),
            'pick_Found':'orange',
            'pickTxt_None':'darkred',
            'pickTxt_Found':'white',
            'side_param_Txt':'silver',
            'bttn_back':(0.15, 0.15, 0.15),
            'build_bttn_back':(0.85, 0.6, 0),
            'drpdwn_back':(0.15, 0.15, 0.15),
            'sub_back':(0.19, 0.19, 0.19)
        }

        self.ui_items = {}
        self.ui_data = {
            'system':None, 'rebuild':True, 'scale_fix':False,
            'camera':None, 'range':"Slider", 'cstm_range':(deci.Decimal('1.0'), deci.Decimal('100.0')),
            'step':deci.Decimal('1.0'), 'pool':0, 'aim_dist':deci.Decimal('0.5'), 'aim_zero_obj':None, 'aimmtx':None,
            'target_color':(0.2, 1.0, 0.0), 'target_select':"Selectable", 'target_size':deci.Decimal('1.0'), 'target_display':True, 'target_obj':None,
            'cross_color':(1.0, 1.0, 0.0), 'cross_select':"Selectable", 'cross_size':deci.Decimal('0.5'), 'cross_calcul':True, 'cross_display':True, 'cross_grp':None, 'cross_obj':None,
            'trail_color':(1.0, 0.0, 0.0), 'trail_select':"Selectable", 'trail_calcul':True, 'trail_display':True, 'trail_grp':None, 'trail_obj':None
        }
        self.callback_hook = None
        self.pick_sel = None
        self.pick_selData = None
        self.pick_ui = None
        self.pick_job = None
        self.is_expanded = True if expanded else False
        # --- Variables ---

        # --- UI ---
        Build_Window( self, SELF_IDX, expanded, True )
        # --- UI ---

#region --- Functions ---
#region - * General *
# Utility
def _Get_WindowIdx( self, multi_windows:bool ): #Return incremented class windows count
    """ Return incremented class windows count """
    global global_win_instances #Declare as global variables to not get replaced by function-local variable with value assignement
    global global_win_count

    idx = 0
    if multi_windows:
        #Look for existing unused index in the global_win_instances list to recycle
        overwrite_none = False
        for c_instance in global_win_instances:
            if c_instance is None:
                overwrite_none = True
                break
            idx+=1
        
        if overwrite_none: # Recycle index
            global_win_instances[idx] = self
        else: # Create new index
            idx = global_win_count
            global_win_count = idx + 1
            global_win_instances.append(self)
    else:
        idx = 0
        if global_win_count == 0: # Create index 0
            global_win_count = 1
            global_win_instances.append(self)
        else: # Overwrite index 0
            old_count = global_win_count
            global_win_instances[idx] = None
            # Create or overwrite index 0 which has been cleared by window's close command
            if global_win_count == 0:
                global_win_count = 1
                global_win_instances.append(self)
            else:
                global_win_count = old_count
                global_win_instances[idx] = self
    return idx

def _Get_Instance( self_idx:int ): #Return class instance object from index as UI commands can't seem to store class instance objects
    """ Return class instance object from index as UI commands can't seem to store class instance objects """
    return global_win_instances[self_idx]

def _Filter_Selection( limit_type ): #Filter selection and return it and the result type
    """
    Filter selection and return it and the result type (0:empty, 1:no match, 2:match all, 3:match last)\n
    ### Parameters:\n
    'limit_type': (str/list/tuple): Types(s) accepted
    """
    sel = cmds.ls( selection=True, showType=True )
    if sel != []:
        if type(limit_type) is str:
            limit_type = [limit_type]
        
        #Separate objects and their showType
        sel_len = len(sel)
        i = 0
        i2 = 0
        t_sel = [[],[]]
        while i < sel_len:
            t_sel[i2].append( sel[i] )
            i2 = 1 if i2 == 0 else 0
            i+=1
        sel = t_sel
        t_sel = None

        #Get how many selection match limit_type
        match_type = 0
        for sel_type in sel[1]:
            if sel_type in limit_type:
                match_type+=1
        
        if match_type == len(sel[1]): #If every selected object match the limit_type
            return sel[0], 2
        elif sel[1][-1] in limit_type: #If last object matches limit_type
            return [sel[0][-1]], 3
        return sel[0], 1
    return sel, 0

def _Create_Locator( self, loc_name:str, loc_parent:str, element_idx:int ): #Create a locator element, include element visibility and size but no other parameters as some are on element grp
    """
    Create a locator element, include element visibility and size but no other parameters as some are on element grp\n
    ### Parameters:\n
    'name' (str): Locator transform name\n
    'parent' (str): Parent name\n
    'element_idx' (int): Sub element index to take values from in ui_data ( 0:Target, 1:Cross, 2:Trail )
    ### Return:
    locator_transform (str)
    """
    prefix = None
    if element_idx == 0:
        prefix = 'target'
    elif element_idx == 1:
        prefix = 'cross'
    else:
        prefix = 'trail'

    locator = cmds.createNode( 'transform', name=loc_name, parent=loc_parent, skipSelect=True )
    if element_idx != 0:
        cmds.setAttr( f'{locator}.visibility', 0 )
    locator_shape = cmds.createNode( 'locator', name=f"{locator}Shape", parent=locator, skipSelect=True )
    #Size
    if element_idx == 0:
        float_size = float(self.ui_data[f'{prefix}_size'])
        cmds.setAttr( f'{locator_shape}.localScale', float_size, float_size, float_size )
    elif element_idx == 1:
        float_size = float( self.ui_data[f'{prefix}_size'] * deci.Decimal('0.01') )
        cmds.setAttr( f'{locator_shape}.localScale', float_size, float_size, float_size )
    else:
        cmds.setAttr( f'{locator_shape}.localScale', 0, 0, 1 )
    return locator

def _Lock_Transf( name:str ): #Lock, hide and set non-keyable transform attributes
    """ Lock, hide and set non-keyable transform attributes """
    transforms = ['translate','rotate','scale']
    axes = ['X','Y','Z']
    for transf in transforms:
        for axis in axes:
            cmds.setAttr( f'{name}.{transf}{axis}', lock=True, keyable=False, channelBox=False )

# UI
def _Clear_WindowClose( self_idx:int, cmd_idx ): #Clear window closeCommand by replacing it with a print command instead
    """
    Clear window closeCommand by replacing it with a print command instead\n
    ### Parameters:\n
    'self_idx' (int): class object index in global_win_instances\n
    'cmd_idx' (int/str): window closeCommand, int ( 0:Empty ) else str
    """
    cmd = None
    if type(cmd_idx) == int:
        if cmd_idx == 0:
            cmd = partial(_Empty)
        else:
            print( f"Unknown cmd_idx", cmd_idx )
    else:
        cmd = cmd_idx
    
    if self_idx > global_win_count:
        cmds.error( f"[ISSUE]: Instance index {self_idx} out of range!", noContext=True )
    cmds.window( global_win_instances[self_idx].WIN_NAME, edit=True, closeCommand=cmd )
    _Pick_Cancel( None, self_idx )

def _Empty(): #Empty function for _Clear_WindowClose()
    """ Empty function for _Clear_WindowClose() """
    pass

def _Build_PickerBttn( parent:str, height:int, field:tuple, sep_width, bttn:tuple, image='colorPickCursor.png' ): #Create a picker button and return it
    """
    Create a picker button and return it\n
    ### Parameters:\n
    'parent' (str): Parent layout name\n
    'height' (int): Height for both elements\n
    'field' (tuple): If not None, text field UI settings ( width(int), defaultText(str), editable(bool), command(str), annotation(str), statusBarMessage(str), backgroundColor(list), dragCallbackCommand(str) )\n
    'sep_width' (None/int): If not None, create separator too at said width\n
    'bttn' (tuple): Button field UI settings ( command(str), annotation(str), statusBarMessage(str), backgroundColor(list), customSize(width, height), dragCallbackCommand(str) )\n
    'image' (str): Bttn image\n
    ### Return:\n
    -If 'field' is None: 'symbolBttn'\n
    -If 'field' is not None: 'txtField', 'symbolBttn'
    """
    txtField = None
    if field is not None:
        if len(field) == 8:
            txtField = cmds.textField(
                height=height, width=field[0],
                editable=field[2], text=field[1],
                changeCommand=field[3], dragCallback=field[7],
                annotation=field[4], statusBarMessage=field[5],
                backgroundColor=field[6],
                parent=parent
            )
        else:
            txtField = cmds.textField(
                height=height, width=field[0],
                editable=field[2], text=field[1],
                changeCommand=field[3],
                annotation=field[4], statusBarMessage=field[5],
                backgroundColor=field[6],
                parent=parent
            )
    if sep_width is not None:
        cmds.separator( height=height, width=sep_width, style='none', parent=parent )
    bttn_wh = (height, height) if len(bttn) == 4 or bttn[4] is None else bttn[4]
    if len(bttn) == 6:
        symbolBttn = cmds.symbolButton(
            height=bttn_wh[1], width=bttn_wh[0],
            image=image, command=bttn[0], dragCallback=bttn[5],
            annotation=bttn[1], statusBarMessage=bttn[2],
            backgroundColor=bttn[3],
            parent=parent
        )
    else:
        symbolBttn = cmds.symbolButton(
            height=bttn_wh[1], width=bttn_wh[0],
            image=image, command=bttn[0],
            annotation=bttn[1], statusBarMessage=bttn[2],
            backgroundColor=bttn[3],
            parent=parent
        )
    if txtField is not None:
        return txtField, symbolBttn
    return symbolBttn

def _Pick_Init( self_idx:int, pick_count:int, result_command, ui_set:str, limit_type=None, skip_deselect=True, ae_check=False, any_sel=False, partial_empty=None ): #Let user pick something
    """
    Let user pick something\n
    ### Parameters:\n
    'self_idx' (int): class object index in global_win_instances\n
    'pick_count' (int): Number of items to pick\n
    'result_command' (function): Command to call once object(s) picked\n
    'ui_set' (str): Call self.pick_ui preset (0:system_picker, 1:camera_picker, 2:camera_picker(+current view))\n
    'limit_type' (None/tuple): If not None, test if already selecting an object of this type and limit picker selection\n
    'skip_deselect' (bool): Don't deselect last item picked\n
    'ae_check' (bool): If limit_type set and existing selection doesn't match, look at current attribute editor tab\n
    'any_sel' (bool): If True return any already selected object regardless of their type\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    self = _Get_Instance( self_idx )

    if self.callback_hook != None:
        cmds.warning( f"[ISSUE]: A picking is already ongoing. To cancel current picking please select any object or node", noContext=True )
        return
    
    #Set self.pick_selData to store extra informations about the picking context
    #if ui_set == 0: #

    #Test if not already selecting uvPin
    if any_sel:
        sel = cmds.ls( selection=True, showType=True )
        if sel != []:
            self.pick_sel = sel
            self.callback_hook = 'picking' #Set a callback hook so not skipped by function
            result_command( self_idx, True )
            return
    if limit_type is not None:
        sel = cmds.ls( selection=True, showType=True )
        found = False
        if sel != []:
            sel, sel_type = _Filter_Selection( limit_type )
            if sel_type == 2 or sel_type == 3:
                found = True
        
        if not found and ae_check:
            sel = mel.eval( '$gAECurrentTab = $gAECurrentTab' )
            if sel != '' and cmds.nodeType( sel ) in limit_type:
                sel = [sel]
                found = True
        
        if found:
            self.pick_sel = sel
            self.callback_hook = 'picking' #Set a callback hook so not skipped by function
            result_command( self_idx, True )
            return
    
    if ui_set == 2: #Camera+current view, if no camera already selected get current view's camera
        current_cam = None
        for panel in cmds.getPanel( type="modelPanel" ): #Get camera from active viewport
            current_cam = cmds.modelEditor( panel, query=True, activeView=True )
            if current_cam:
                current_cam = cmds.modelEditor( panel, query=True, camera=True )
                break
        if current_cam is not None:
            if type(cmds.getAttr( f"{current_cam.rsplit('|',1)[1]}.nodeState" )) != list: #If there is only one camera at this name, remove fullpath before it
                current_cam = current_cam.rsplit('|',1)[1]
            self.pick_sel = [current_cam]
            self.callback_hook = 'picking' #Set a callback hook so not skipped by function
            result_command( self_idx, True )
            return
    
    if ui_set == 0:
        self.pick_ui = ( self.ui_items['sys_picker_symbolBttn'], self.THEME['sys_pick_back_on'], self.THEME['sys_pick_back_off'] )
    elif ui_set == 1:
        self.pick_ui = ( self.ui_items['camera_picker_symbolBttn'], self.THEME['pick_back_on'], self.THEME['pick_back_off'] )
    #Prepare callback for end function
    cmds.callbacks( addCallback=result_command, hook='picking', owner='Local_MotionTrail' )
    self.callback_hook = 'picking'
    #Start picking
    _Pick_Selection( self_idx, pick_count, limit_type, skip_deselect )

def _Pick_Init_Callback( self_idx:int, pick_count:int, result_command, ui_set:str, limit_type=None, skip_deselect=True, ae_check=False, any_sel=False,    drgCllBck_drgCtrl=None, drgCllBck_x=None, drgCllBck_y=None, drgCllBck_mod=None ):
    """
    Let user pick something\n
    ### Parameters:\n
    'self_idx' (int): class object index in global_win_instances\n
    'pick_count' (int): Number of items to pick\n
    'result_command' (function): Command to call once object(s) picked\n
    'ui_set' (str): Call self.pick_ui preset (0:system_picker, 1:camera_picker, 2:camera_picker(+current view))\n
    'limit_type' (None/tuple): If not None, test if already selecting an object of this type and limit picker selection\n
    'skip_deselect' (bool): Don't deselect last item picked\n
    'ae_check' (bool): If limit_type set and existing selection doesn't match, look at current attribute editor tab\n
    'any_sel' (bool): If True return any already selected object regardless of their type\n
    'drgCllbck...' parameters required when using a function object in a Maya UI dragCallback argument
    """
    _Pick_Init( self_idx, pick_count, result_command, ui_set, limit_type, skip_deselect, ae_check, any_sel )

def _Pick_Selection( self_idx:int, pick_count_target=1, limit_type=None, skip_deselect=False, _looping=False, _pick_count=0 ): #Start a selection picker
    """
    Start a selection picker\n
    ### Parameters:\n
    'pick_count_target' (int): Amount of selection expected to pick\n
    'limit_type' (str/list): Type(s) to limit selection from\n
    'skip_deselect' (bool): Skip deselecting after picking\n
    '_looping' (bool): Internal, used by the script to call a new pick until target selection count without recreating values\n
    '_pick_count' (int): Internal, used by the script to maintain selection count value\n
    ### Also requires to set values for:\n
    'self.callback_hook' (str): callback hook name\n
    'self.pick_ui' (tuple): ( symbolBttn, backgroundColorHighlight, backgroundColorDefault )
    """
    self = _Get_Instance( self_idx )

    if not _looping: #Init picker
        cmds.symbolButton( self.pick_ui[0], edit=True, backgroundColor=self.pick_ui[1] ) #Highlight picker UI
        cmds.select( clear=True )
        if pick_count_target > 1:
            self.pick_sel = []
    
    limit_type = f"'{limit_type}'" if type(limit_type) == str else limit_type
    self.pick_job = cmds.scriptJob( #Check next selection
        runOnce=True,
        event=['SelectionChanged',partial(_Pick_Selection_Extract, self_idx, _pick_count, pick_count_target, limit_type, skip_deselect)], #Note: Not conditionTrue 'SomethingSelect' as it seems to require deselection to count again as True
        protected=True, parent=self.WINDOW
    )

def _Pick_Selection_Extract( self_idx:int, pick_count:int, pick_count_target:int, limit_type, skip_deselect ): #Called after selecting while running _Pick_Selection()
    """ Called after selecting while running _Pick_Selection() """
    self = _Get_Instance( self_idx )

    self.pick_job = None
    sel = None
    if limit_type is not None:
        sel, sel_type = _Filter_Selection( limit_type )

        if sel_type == 0:
            cmds.warning( f"[ISSUE]: Selection empty!", noContext=True )
        elif sel_type == 1:
            cmds.warning( f"[ISSUE]: {sel} do{'es' if len(sel) < 2 else ''}n't match {'type' if type(limit_type) is str else 'types'} '{limit_type}' !", noContext=True )
            sel = []
    else:
        sel = cmds.ls( selection=True )
    
    if sel != []:
        if pick_count_target > 1:
            self.pick_sel.append(sel)
        else:
            self.pick_sel = sel
        if not skip_deselect:
            cmds.select( clear=True )
    
    pick_count += 1
    if pick_count >= pick_count_target: #Picking done, clear data, reselect old selection and call end function via it's callback
        call_hook = f'{self.callback_hook}'
        cmds.symbolButton( self.pick_ui[0], edit=True, backgroundColor=self.pick_ui[2] )
        cmds.callbacks( self_idx, executeCallbacks=True, hook=call_hook ) #Call end function
        cmds.callbacks( clearCallbacks=True, hook=call_hook, owner='Local_MotionTrail' )
    else:
        _Pick_Selection( self_idx, pick_count_target, limit_type, skip_deselect, True, pick_count ) #Continue picking

def _Pick_Cancel( self, self_idx:int ): #Stop picking
    """ Stop picking """
    self = _Get_Instance( self_idx )
    if self.callback_hook is None:
        return
    if self.pick_job is not None and cmds.scriptJob( exists=self.pick_job ):
        cmds.scriptJob( kill=self.pick_job, force=True )
    cmds.callbacks( clearCallbacks=True, owner='Local_MotionTrail' )
    self.callback_hook = None
    self.pick_sel = None
    self.pick_selData = None
    self.pick_ui = None
    cmds.inViewMessage( message="<font color=darkorange>Picking cancelled!</font color>", position="botCenter", fade=True, fadeOutTime=300 )
    print( "[INFO]: Picking cancelled!" )

def _Build_DecimalTextField( parent:str, height:int, field:tuple, sep_width:int, bttns:tuple, background_color:list ): #Create an textField with up and down arrow buttons
    """
    Create an textField with up and down arrow buttons\n
    ### Parameters:\n
    'parent' (str): Parent layout name\n
    'height' (int): Height for both elements\n
    'field' (tuple): ( width(int), editable(bool), change_command(str), text(str), annotation(str), statusBarMessage(str) )\n
    'sep_width' (None/int): If not None, create separator too at said width\n
    'bttns' (tuple): ( size(int), top_offset(int), down_offset(int), command_up(str), command_down(str) )\n
    'background_color' (list): Maya UI backgroundColor\n
    ### Return:\n
    'intFieldCtrl'
    """
    textFieldCtrl = cmds.textField(
        height=height, width=field[0],
        editable=field[1], changeCommand=field[2], text=field[3],
        annotation=field[4], statusBarMessage=field[5],
        backgroundColor=background_color,
        parent=parent
    )
    
    if sep_width is not None:
        cmds.separator( height=height, width=sep_width, style='none', parent=parent )
    
    bttns_clmnLyt = cmds.rowColumnLayout(
        height=height+bttns[1], width=bttns[0]+2,
        numberOfRows=2, rowAttach=( (1, 'top', 0), (2, 'top', bttns[2]*2) ),
        parent=parent
    )
    cmds.symbolButton(
        height=bttns[0], width=bttns[0],
        image='moveUVUp.png', command=bttns[3],
        backgroundColor=background_color,
        parent=bttns_clmnLyt
    )
    cmds.symbolButton(
        height=bttns[0], width=bttns[0],
        image='moveUVDown.png', command=bttns[4],
        backgroundColor=background_color,
        parent=bttns_clmnLyt
    )
    return textFieldCtrl

def _Check_StrToFloat( value:str ): #Check text value fits float value format
    """
    Check text value fits float value format. Do not support math functions\n
    ### Parameters:\n
    'value' (str): Text value to check\n
    ### Return:\n
    value(str), issue_str(None/str)
    """
    value = value.replace(',','.')
    issue_str = None
    if value.count('.') > 1:
        value = None
        issue_str = "More than one decimal separator!"
    elif value.count('-') > 1:
        value = None
        issue_str = "More than one minus sign!"
    elif '-' in value and value[0] != '-':
        value = None
    else:
        value_clear = value.replace('.','',1).replace('-','',1)
        if value_clear == '':
            value = None
            issue_str = "No decimal!"
        elif not value_clear.isdecimal:
            value = None
            issue_str = "Non-decimal character(s) found!"
    return value, issue_str

def _Build_IntField( parent:str, height:int, field:tuple, sep_width:int, bttns:tuple, background_color:list ): #Create an intField with up and down arrow buttons
    """
    Create an intField with up and down arrow buttons\n
    ### Parameters:\n
    'parent' (str): Parent layout name\n
    'height' (int): Height for both elements\n
    'field' (tuple): ( width(int), editable(bool), change_command(str), value(int), min_value(None/int), max_value(None/int), annotation(str), statusBarMessage(str) )\n
    'sep_width' (None/int): If not None, create separator too at said width\n
    'bttns' (tuple): ( size(int), top_offset(int), down_offset(int), command_up(str), command_down(str) )\n
    'background_color' (list): Maya UI backgroundColor\n
    ### Return:\n
    'intFieldCtrl'
    """
    intFieldCtrl = None
    if field[4] is None and field[5] is None: #No min max value
        intFieldCtrl = cmds.intField(
            height=height, width=field[0],
            editable=field[1], changeCommand=field[2], value=field[3],
            annotation=field[6], statusBarMessage=field[7],
            backgroundColor=background_color,
            parent=parent
        )
    elif field[5] is None: #min
        intFieldCtrl = cmds.intField(
            height=height, width=field[0],
            editable=field[1], changeCommand=field[2], value=field[3], minValue=field[4],
            annotation=field[6], statusBarMessage=field[7],
            backgroundColor=background_color,
            parent=parent
        )
    else: #min max
        intFieldCtrl = cmds.intField(
            height=height, width=field[0],
            editable=field[1], changeCommand=field[2], value=field[3], minValue=field[4], maxValue=field[5],
            annotation=field[6], statusBarMessage=field[7],
            backgroundColor=background_color,
            parent=parent
        )
    
    if sep_width is not None:
        cmds.separator( height=height, width=sep_width, style='none', parent=parent )
    
    bttns_clmnLyt = cmds.rowColumnLayout(
        height=height+bttns[1], width=bttns[0]+2,
        numberOfRows=2, rowAttach=( (1, 'top', 0), (2, 'top', bttns[2]*2) ),
        parent=parent
    )
    cmds.symbolButton(
        height=bttns[0], width=bttns[0],
        image='moveUVUp.png', command=bttns[3],
        backgroundColor=background_color,
        parent=bttns_clmnLyt
    )
    cmds.symbolButton(
        height=bttns[0], width=bttns[0],
        image='moveUVDown.png', command=bttns[4],
        backgroundColor=background_color,
        parent=bttns_clmnLyt
    )
    return intFieldCtrl

def _Build_SplitSep( parent:str, height:int, sep_width:int, font_size:int ): #Create special / separator
    """ Create special / separator """
    cmds.separator( height=height, width=sep_width, style='none', parent=parent )
    cmds.text( height=height, label=f"<font size={font_size}><b/>/</b></font>", parent=parent )
    cmds.separator( height=height, width=sep_width, style='none', parent=parent )

def _Build_SubLine( self, line_parent:str, line_data:tuple, color_data:tuple, select_data:tuple, size_data, calcul_data:tuple, display_data:tuple, clear_command:str ): #Build sub element UI line
    """
    Build sub element UI line\n
    ### Parameters:\n
    'line_parent' (str): Partent of the line\n
    'line_data' (tuple): ( image(str), command(None/str), dragCallback(None/str), annotation(str), statusBarMessage(str) )\n
    'color_data' (tuple): ( command(str), backgroundColor(tuple) )\n
    'select_data' (tuple): ( command(str), value(str) )\n
    'size_data' (None/tuple): If not None, ( field_command(str), up_command(str), down_command(str), value(int) )\n
    'calcul_data' (None/tuple): If not None, ( on_command(str), off_command(str), value(bool) )\n
    'display_data' (tuple): ( on_command(str), off_command(str), value(bool) )\n
    'clear_command' (None/str): If not None, Command for clear symbolCheckBox\n
    ### Return:\n
    color_bttn, select_opMenu, size_decimalTextField, calcul_symbolChckBx, display_symbolChckBx
    """
    sub_line_rowLyt = cmds.rowLayout(
        height=37,
        numberOfColumns=20,
        parent=line_parent
    )
    
    sub_offset_rowClmnLyt = cmds.rowLayout( # Bottom rowClmnLyt
        height=37,
        numberOfColumns=3,
        rowAttach=((1, 'bottom', 0), (2, 'bottom', 0), (3, 'bottom', 0)),
        parent=sub_line_rowLyt
    )
    #Line button
    if line_data[1] is None and line_data[2] is None:
        cmds.symbolButton(
            height=30, width=30,
            image=line_data[0], annotation=line_data[3], statusBarMessage=line_data[4],
            parent=sub_offset_rowClmnLyt
        )
    elif line_data[1] is not None and line_data[2] is not None: #Command and dragCallback
        cmds.symbolButton(
            height=30, width=30,
            image=line_data[0], annotation=line_data[3], statusBarMessage=line_data[4], command=line_data[1], dragCallback=line_data[2],
            parent=sub_offset_rowClmnLyt
        )
    elif line_data[2] is None: #Command
        cmds.symbolButton(
            height=30, width=30,
            image=line_data[0], annotation=line_data[3], statusBarMessage=line_data[4], command=line_data[1],
            parent=sub_offset_rowClmnLyt
        )
    else: #DragCallback
        cmds.symbolButton(
            height=30, width=30,
            image=line_data[0], annotation=line_data[3], statusBarMessage=line_data[4], dragCallback=line_data[2],
            parent=sub_offset_rowClmnLyt
        )
    cmds.separator( height=35, width=40, style='none', parent=sub_offset_rowClmnLyt )
    #Color
    color_bttn = cmds.button(
        height=30, width=80, label="",
        command=color_data[0],
        annotation="Change the element's color", statusBarMessage="Change the element's color",
        backgroundColor=color_data[1],
        parent=sub_offset_rowClmnLyt
    )

    # / #
    _Build_SplitSep( sub_line_rowLyt, 35, 20, 7 )
    # / #

    sub_offset_rowClmnLyt = cmds.rowLayout( # Bottom rowClmnLyt
        height=37,
        numberOfColumns=1,
        rowAttach=(1, 'bottom', 0),
        parent=sub_line_rowLyt
    )
    #Seletable
    select_opMenu = cmds.optionMenu(
        height=30, width=150,
        maxVisibleItems=10, changeCommand=select_data[0],
        annotation="Change the element's selectability\n\nNote: 'Non selectable' locks the color in black", statusBarMessage="Change the element's electability  -  Note: 'Non selectable' the color in black",
        backgroundColor=self.THEME['drpdwn_back'],
        parent=sub_offset_rowClmnLyt
    )
    cmds.menuItem( label="Selectable", parent=select_opMenu )
    cmds.menuItem( label="Non selectable", parent=select_opMenu )
    cmds.optionMenu( select_opMenu, edit=True, value=select_data[1] )

    if size_data is None:
        cmds.separator( height=30, width=54, style='none', parent=sub_line_rowLyt )
    else:
        # / #
        _Build_SplitSep( sub_line_rowLyt, 35, 20, 7 )
        # / #

    sub_offset_rowClmnLyt = cmds.rowLayout( # Bottom rowClmnLyt
        height=37,
        numberOfColumns=8,
        rowAttach=((1, 'bottom', 0), (2, 'bottom', 0), (3, 'bottom', 0), (4, 'bottom', 0), (5, 'bottom', 0), (6, 'bottom', 0), (7, 'bottom', 0), (8, 'bottom', 0)),
        parent=sub_line_rowLyt
    )
    #Size
    size_decimalTextField = None
    if size_data is None:
        cmds.separator( height=30, width=66, style='none', parent=sub_offset_rowClmnLyt )
    else:
        size_decimalTextField = _Build_DecimalTextField(
            sub_offset_rowClmnLyt, 30,
            ( 50, True, size_data[0], size_data[3], "Change the element's size", "Change the element's size" ),
            None,
            ( 12, 0, 2, size_data[1], size_data[2] ),
            self.THEME['bttn_back']
        )
    cmds.separator( height=30, width=80, style='none', parent=sub_offset_rowClmnLyt )
    #Calculate
    if calcul_data is None:
        calcul_symbolChckBx = cmds.separator( height=30, width=30, style='none', parent=sub_offset_rowClmnLyt )
    else:
        calcul_symbolChckBx = cmds.symbolCheckBox(
            height=30, width=30,
            onImage='confirm.png', offImage='hotkeyFieldClear.png', highlightColor=self.THEME['sub_back'],
            onCommand=calcul_data[0], offCommand=calcul_data[1], value=calcul_data[2],
            annotation="Calculate this element", statusBarMessage="Calculate this element",
            parent=sub_offset_rowClmnLyt
        )
    cmds.separator( height=30, width=40, style='none', parent=sub_offset_rowClmnLyt )
    #Display
    display_symbolChckBx = cmds.symbolCheckBox(
        height=30, width=30,
        onImage='eye.png', offImage='Bool_Hidden.png', highlightColor=self.THEME['sub_back'],
        onCommand=display_data[0], offCommand=display_data[1], value=display_data[2],
        annotation="Display this element", statusBarMessage="Display this element",
        parent=sub_offset_rowClmnLyt
    )
    cmds.separator( height=30, width=40, style='none', parent=sub_offset_rowClmnLyt )
    #Clear
    if clear_command is not None:
        cmds.symbolButton(
            height=30, width=30,
            image='delete.png',
            command=clear_command,
            annotation="Clear this element", statusBarMessage="Clear this element",
            parent=sub_offset_rowClmnLyt
        )
    return color_bttn, select_opMenu, size_decimalTextField, calcul_symbolChckBx, display_symbolChckBx
#endregion - * General *

#region - * UI/Features *
def _Select_Callback( self_idx:int, select_idx:int,    drgCllBck_drgCtrl=None, drgCllBck_x=None, drgCllBck_y=None, drgCllBck_mod=None ): #Select node/object from data
    """
    Select node/object from data\n
    ### Parameters:\n
    'select_idx' (int): Data idx ( 0:system, 1:camera, 2:target )\n
    'drgCllbck...': parameters required when using a function object in a Maya UI dragCallback argument
    """
    self = _Get_Instance( self_idx )
    node = None
    if select_idx == 0:
        node = self.ui_data['system']
    elif select_idx == 1:
        node = self.ui_data['camera']
    elif select_idx == 2:
        node = self.ui_data['target_obj']
    
    if node is not None and node != 'None':
        cmds.select( node, replace=True )
    cmds.setFocus( '' ) #Remove focus from window

def _Switch_MainBttn( self, state:int ): #Switch between the main buttons
    """
    Switch between the main buttons\n
    ### Parameters:\n
    'state' (int): Main buton state ( 0:Calculate, 1:Build system )
    """
    if state == 0:
        cmds.symbolButton( self.ui_items['buildsys_symbolBttn'], edit=True, visible=False )
        cmds.symbolButton( self.ui_items['calculate_symbolBttn'], edit=True, visible=True )
    else:
        cmds.symbolButton( self.ui_items['calculate_symbolBttn'], edit=True, visible=False )
        cmds.symbolButton( self.ui_items['buildsys_symbolBttn'], edit=True, visible=True )

# System
def _Pick_System_Done( self_idx, skip_check=True ): #End function for geometry pick
    """ End function for geometry pick """
    self_idx = int(self_idx)
    self = _Get_Instance( self_idx )
    if self.callback_hook is not None: #Prevent function called twice
        self.callback_hook = None
    else:
        return
    
    if skip_check or (self.pick_sel != [] and self.pick_sel is not None):
        _Set_System( self, self_idx, True, self.pick_sel[-1] )
    self.pick_sel = None
    self.pick_selData = None
    self.pick_ui = None

def _Set_System( self, self_idx:int, pick=False, node_name=None, partial_empty=None ): #Set system value from textField and picker
    """
    Set system's value\n
    ### Parameters:\n
    'pick' (bool): If True skip rechecking for node existing and update textField once done\n
    'node_name' (None/str): Selection picked node if 'pick' is True, else getting it from the textField's text\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    if self is None:
        self = _Get_Instance( self_idx )
    
    txtField = self.ui_items['sys_picker_txtField']
    camera = None
    is_new = False
    if not pick: #If not pick, get node name from textField
        node_name = cmds.textField( txtField, query=True, text=True )
        
        if node_name == '':
            _Set_System_Revert(self)
            return
        elif node_name == 'None':
            _Set_System_Revert(self)
            cmds.error( f"[ISSUE]: 'None' can't be set as a system name!", noContext=True )
        if node_name is None or not cmds.objExists( node_name ): #Check if node exists, if not guess it as a new system name
            is_new = True
    
    if pick or (not is_new and cmds.nodeType( node_name ) == 'transform'): #Find if selection matches system root, camera or target
        children = cmds.listRelatives( node_name, children=True, fullPath=True ) if '|' in node_name else cmds.listRelatives( node_name, children=True )
        if children is not None:
            sys_expected_children = { f'{node_name}_target_ref', f'{node_name}_aim', f'{node_name}_cross_grp', f'{node_name}_trail_grp' }
            is_system_root = False
            is_camera = False
            has_trsnf_child = False
            trnsf_children = []
            is_locator = False

            for child in children:
                if child in sys_expected_children:
                    is_system_root = True
                child_type = cmds.nodeType( child ).lower()
                if child_type == 'transform': #Could be system root under camera if there is also a child being camera's shape
                    has_trsnf_child = True
                    trnsf_children.append( child ) #In a list in case there are multiple transforms under the camera
                elif child_type == 'camera' or'camera' in child_type: #In case it's a custom camera, which type hopefully contains 'camera'
                    is_camera = True
                elif child_type == 'locator':
                    is_locator = True
            
            if not is_system_root: #Not system, look if this may be it's camera or target locator
                if not is_camera and not is_locator: #No match
                    if not pick:
                        _Set_System_Revert(self)
                    cmds.error( f"[ISSUE]: Couldn't recognize '{node_name}' as system root, camera or system target!", noContext=True )
                
                if is_camera: #Check if there is one system under camera
                    if not has_trsnf_child:
                        if not pick:
                            _Set_System_Revert(self)
                        cmds.error( f"[ISSUE]: '{node_name}' recognized as a camera but no system found under it!", noContext=True )
                    
                    sys_found = False
                    #Check each found transform children if they match system root
                    for child in trnsf_children:
                        sub_children = cmds.listRelatives( child, children=True, fullPath=True ) if '|' in child else cmds.listRelatives( child, children=True )
                        
                        if sub_children is None:
                            continue
                        for sub_child in sub_children: #Check sub children if they match system target object name or aim object name
                            if sub_child == f'{child}_target_loc' or sub_child == f'{child}_aim':
                                sys_found = True
                                camera = node_name #Keep camera name for _Load_System
                                node_name = child #Set system root to node_name
                                break
                    
                    if not sys_found: #No match
                        if not pick:
                            _Set_System_Revert(self)
                        cmds.error( f"[ISSUE]: '{node_name}' recognized as a camera but no system found under it!", noContext=True )
                
                if is_locator: #Check if may be the target locator parented under the system
                    if not node_name.endswith('_target_loc'):
                        if not pick:
                            _Set_System_Revert(self)
                        cmds.error( f"[ISSUE]: '{node_name}' recognized as a locator name but doesn't match target_loc naming!", noContext=True )
                    
                    loc_parent = cmds.listRelatives( node_name, parent=True, fullPath=True ) if '|' in node_name else cmds.listRelatives( node_name, parent=True )
                    sys_found = False
                    if loc_parent is not None: #Check if parent above locator has children matching system names
                        loc_parent = loc_parent[-1]
                        parent_children = cmds.listRelatives( loc_parent, children=True, fullPath=True ) if '|' in node_name else cmds.listRelatives( loc_parent, children=True )

                        if parent_children is not None:
                            for parent_child in parent_children:
                                if parent_child == f'{loc_parent}_target_loc' or parent_child == f'{loc_parent}_aim':
                                    sys_found = True
                                    node_name = loc_parent #Set system root to node_name
                                    break
                    
                    if not sys_found: #No match
                        if not pick:
                            _Set_System_Revert(self)
                        cmds.error( f"[ISSUE]: '{node_name}' recognized as a locator but not as part of a system!", noContext=True )
        else:
            cmds.error( f"[ISSUE]: Couldn't recognize '{node_name}' as system root, camera or system target!", noContext=True )
    
    #Store value and update UI
    self.ui_data['system'] = node_name
    if pick:
        cmds.textField( txtField, edit=True, text=node_name )
    
    if is_new: #New system name
        _Load_System( self, True, camera )
    else: #System exists, update other UI values
        _Load_System( self, False, camera )

def _Set_System_Revert( self ): #Revert system textField to data value
    """ Revert system textField to data value """
    old_value = self.ui_data['system']
    if old_value is None:
        old_value = 'None'
    cmds.textField( self.ui_items['sys_picker_txtField'], edit=True, text=old_value )

def _Set_Hide( self_idx:int, hide:bool, partial_empty=None ): #Hide system
    """ Hide system """
    self = _Get_Instance( self_idx )
    
    hide = 0 if hide else 1
    if self.ui_data['system'] is not None and cmds.objExists( self.ui_data['system'] ):
        cmds.setAttr( f"{self.ui_data['system']}.visibility", hide )

def _Set_Rebuild( self_idx:int, value:bool, update_ui=False, partial_empty=None ): #Set rebuild value
    """ Set rebuild value """
    self = _Get_Instance( self_idx )
    self.ui_data['rebuild'] = value
    if update_ui:
        cmds.symbolCheckBox( self.ui_items['rebuild_symbolChckBx'], edit=True, value=value )

def _Set_Scale_Fix( self_idx:int, value:bool, partial_empty=None ): #Set scale fix value
    """ Set scale fix value """
    self = _Get_Instance( self_idx )
    self.ui_data['scale_fix'] = value

def _Pick_Camera_Done( self_idx, skip_check=True ): #End function for camera pick
    """ End function for camera pick """
    self_idx = int(self_idx)
    self = _Get_Instance( self_idx )
    if self.callback_hook is not None: #Prevent function called twice
        self.callback_hook = None
    else:
        return
    
    if skip_check or (self.pick_sel != [] and self.pick_sel is not None):
        _Set_Camera( self, self_idx, True, self.pick_sel[-1] )
    self.pick_sel = None
    self.pick_selData = None
    self.pick_ui = None

def _Set_Camera( self, self_idx:int, pick=False, node_name=None, partial_empty=None ): #Set camera value from textField and picker
    """
    Set camera value from textField and picker\n
    ### Parameters:\n
    'pick' (bool): If True skip rechecking for node existing and update textField once done\n
    'node_name' (None/str): Selection picked node if 'pick' is True, else getting it from the textField's text\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    if self is None:
        self = _Get_Instance( self_idx )
    
    txtField = None if not self.is_expanded else self.ui_items['camera_picker_txtField']
    if not pick and self.is_expanded:
        node_name = cmds.textField( txtField, query=True, text=True )

        if node_name is None or not cmds.objExists( node_name ): #Check if node exists, if not revert to old value
            old_value = self.ui_data['camera']
            if old_value is None:
                old_value = 'None'
            cmds.textField( txtField, edit=True, text=old_value )
            cmds.error( f"[ISSUE]: Node '{node_name}' not found!", noContext=True )
    
    camera_found = False
    node_type = cmds.nodeType( node_name )
    if node_type == 'transform': #Check if a child shape matches camera type
        children = cmds.listRelatives( node_name, children=True, shapes=True, fullPath=True ) if '|' in node_name else cmds.listRelatives( node_name, children=True, shapes=True )
        if children is not None:
            for child in children:
                child_type = cmds.nodeType( child )
                if child_type == 'camera' or 'camera' in child_type.lower():
                    camera_found = True
                    break
    elif node_type == 'camera' or 'camera' in node_type.lower():
        camera_found = True
    
    if not camera_found: #If doesn't seem to be a camera, ask if user still want it set as such
        confirm_result = cmds.confirmDialog(
            title="Set camera",
            message=f"Warning! '{node_name}' may not be a camera!\n\nDo you still want to set it ?",
            button=["Yes","No"], defaultButton="Yes", cancelButton="No", dismissString="No"
        )
        if confirm_result == "No":
            if pick:
                return
            else:
                old_value = self.ui_data['camera']
                if old_value is None:
                    old_value = 'None'
                if self.is_expanded:
                    cmds.textField( txtField, edit=True, text=old_value )
                return
    
    #Store value and update UI
    self.ui_data['camera'] = node_name
    if pick and self.is_expanded:
        cmds.textField( txtField, edit=True, text=node_name )

# System Extra
def _Set_Range( self_idx:int, partial_empty=None ): #Set element's range state
    """ Set range's state """
    self = _Get_Instance(self_idx)

    element_value = 'range'
    element_ui = 'range_opMenu'

    value = cmds.optionMenu( self.ui_items[element_ui], query=True, value=True )
    self.ui_data[element_value] = value
    _Update_CstmRangeUI( self, value )

def _Update_CstmRangeUI( self, value=None ): #Show or hide custom range UI depending on range's value
    """ Show or hide custom range UI depending on range's value """
    if value is None:
        value = self.ui_data['range']
    if value == "Custom":
        cmds.rowLayout( self.ui_items['cstm_range_rowLyt'], edit=True, visible=True )
    else:
        cmds.rowLayout( self.ui_items['cstm_range_rowLyt'], edit=True, visible=False )

def _Set_CstmRange( self_idx:int, field_idx:int, arrow_idx=None, partial_empty=None ): #Set custom range value
    """ Set custom range value """
    self = _Get_Instance(self_idx)

    element_value = 'cstm_range'
    element_ui = None
    if field_idx == 0:
        element_ui = 'cstm_range_s_textField'
    else:
        element_ui = 'cstm_range_e_textField'

    value = None
    if arrow_idx is None:
        value = cmds.textField( self.ui_items[element_ui], query=True, text=True )
        #Check value match float format
        value, issue_str = _Check_StrToFloat( value )
        if value is None:
            cmds.textField( self.ui_items[element_ui], edit=True, text=self.ui_data[element_value][field_idx] )
            if issue_str is not None:
                cmds.error( f"[ISSUE]: {issue_str}", noContext=True )
            else:
                return
        #Try to convert string to float, with decimal.Decimal() to make sure
        try:
            value = deci.Decimal(f'{value}')
        except Exception as exception_name:
            cmds.textField( self.ui_items[element_ui], edit=True, text=self.ui_data[element_value][field_idx] )
            cmds.error( f"[ISSUE]: Invalid float value (Exception: {exception_name}, type: {type(exception_name)})", noContext=True )
    else:
        value = self.ui_data[element_value][field_idx]
        value = deci.Decimal(f'{value}') + deci.Decimal('1.0') if arrow_idx == 0 else deci.Decimal(f'{value}') - deci.Decimal('1.0') #Use decimal.Decimal to prevent floating point issues
    
    #Reconvert to tuple
    self.ui_data[element_value] = ( value, self.ui_data[element_value][1] ) if field_idx == 0 else ( self.ui_data[element_value][0], value )
    cmds.textField( self.ui_items[element_ui], edit=True, text=value )

def _Set_Step( self_idx:int, arrow_idx=None, partial_empty=None ): #Set step
    """ Set step """
    self = _Get_Instance(self_idx)

    element_value = 'step'
    element_ui = 'step_textField'

    value = None
    if arrow_idx is None:
        value = cmds.textField( self.ui_items[element_ui], query=True, text=True )
        #Check value match float format
        value, issue_str = _Check_StrToFloat( value )
        if value is None:
            cmds.textField( self.ui_items[element_ui], edit=True, text=self.ui_data[element_value] )
            if issue_str is not None:
                cmds.error( f"[ISSUE]: {issue_str}", noContext=True )
            else:
                return
        #Try to convert string to float, with decimal.Decimal() to make sure
        try:
            value = deci.Decimal(f'{value}')
        except Exception as exception_name:
            cmds.textField( self.ui_items[element_ui], edit=True, text=self.ui_data[element_value] )
            cmds.error( f"[ISSUE]: Invalid float value (Exception: {exception_name}, type: {type(exception_name)})", noContext=True )
    else: #If from arrows, increase or decrease
        if arrow_idx == 0:
            value = self.ui_data[element_value] + 1
        else:
            value = self.ui_data[element_value] - 1

    self.ui_data[element_value] = value
    cmds.textField( self.ui_items[element_ui], edit=True, text=f'{value}' )

def _Set_Pool( self_idx:int, arrow_idx=None, partial_empty=None ): #Set pool
    """ Set pool """
    self = _Get_Instance(self_idx)

    element_value = 'pool'
    element_ui = 'pool_intField'

    value = cmds.intField( self.ui_items[element_ui], query=True, value=True )
    if arrow_idx == 0:
        value+=1
    elif arrow_idx == 1:
        value-=1
    self.ui_data[element_value] = value
    
    if arrow_idx is not None and self.is_expanded: #If from arrows, update intField
        cmds.intField( self.ui_items[element_ui], edit=True, value=value )

def _Set_Cam_Dist( self_idx:int, arrow_idx=None, partial_empty=None ): #Set camera distance
    """
    Set camera distance\n
    ### Parameters:\n
    'arrow_idx' (None/int): If from arrows, 0:up and 1:down\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    self = _Get_Instance(self_idx)

    element_value = 'aim_dist'
    element_ui = 'aim_dist_textField'
    
    value = None
    if arrow_idx is None:
        value = cmds.textField( self.ui_items[element_ui], query=True, text=True )
        #Check value match float format
        value, issue_str = _Check_StrToFloat( value )
        if value is None:
            cmds.textField( self.ui_items[element_ui], edit=True, text=self.ui_data[element_value] )
            if issue_str is not None:
                cmds.error( f"[ISSUE]: {issue_str}", noContext=True )
            else:
                return
        #Try to convert string to float, with decimal.Decimal() to make sure
        try:
            value = deci.Decimal(f'{value}')
        except Exception as exception_name:
            cmds.textField( self.ui_items[element_ui], edit=True, text=self.ui_data[element_value] )
            cmds.error( f"[ISSUE]: Invalid float value (Exception: {exception_name}, type: {type(exception_name)})", noContext=True )
    else: #If from arrows, increase or decrease
        if arrow_idx == 0:
            value = self.ui_data[element_value] + 1
        else:
            value = self.ui_data[element_value] - 1

    self.ui_data[element_value] = value
    cmds.textField( self.ui_items[element_ui], edit=True, text=f'{value}' )
    if self.ui_data['aim_zero_obj'] is not None and cmds.objExists( self.ui_data['aim_zero_obj'] ):
        cmds.setAttr( f"{self.ui_data['aim_zero_obj']}.translateX", float(value) )

# Sub elements
def _Set_Color( self_idx:int, line_idx:int, from_obj=False, result_color=None, partial_empty=None ): #Create colorEdidtor window to set element's color
    """
    Create colorEdidtor window to set element's color\n
    ### Parameters:\n
    'line_idx' (int): Element index ( 0:target, 1:cross, 2:trail )\n
    'from_obj' (bool): Called from system load, only update ui and data\n
    'result_color' (list): With 'from_obj', color value from object\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    self = _Get_Instance(self_idx)

    #Get screen coordinate for the UI
    window_position = cmds.window( self.WIN_NAME, query=True, topLeftCorner=True )
    element_value = None
    element_ui = None
    element_obj = None
    if line_idx == 0:
        window_position = ( window_position[1]+90, window_position[0]+130 )
        element_value = 'target_color'
        element_ui = 'target_color_bttn'
        element_obj = 'target_obj'
    elif line_idx == 1:
        window_position = ( window_position[1]+90, window_position[0]+185 )
        element_value = 'cross_color'
        element_ui = 'cross_color_bttn'
        element_obj = 'cross_grp'
    else:
        window_position = ( window_position[1]+90, window_position[0]+240 )
        element_value = 'trail_color'
        element_ui = 'trail_color_bttn'
        element_obj = 'trail_grp'
    #Build the UI
    if not from_obj:
        result_color = cmds.colorEditor(
            mini=True, position=( window_position[0], window_position[1] ), rgb=self.ui_data[element_value]
        )
        #Convert result string to rgb
        result_color = result_color.split(' ')
        result_color = ( float(result_color[1]), float(result_color[3]), float(result_color[5]) )
        
        if self.ui_data[element_obj] is not None and cmds.objExists( self.ui_data[element_obj] ):
            cmds.setAttr( f'{self.ui_data[element_obj]}.overrideColorRGB', result_color[0], result_color[1], result_color[2] )
            if line_idx == 0:
                cmds.setAttr( f'{self.ui_data[element_obj]}.outlinerColor', result_color[0], result_color[1], result_color[2] )
    else:
        result_color = tuple(result_color[0])
    
    if self.is_expanded:
        cmds.button( self.ui_items[element_ui], edit=True, backgroundColor=result_color )
    self.ui_data[element_value] = result_color

def _Set_Selectable( self_idx:int, line_idx:int, from_obj=False, value=None, partial_empty=None ): #Set element's selectable state
    """
    Set element's selectable state\n
    ### Parameters:\n
    'line_idx' (int): Element index ( 0:target, 1:cross, 2:trail )\n
    'from_obj' (bool): Called from system load, only update ui and data\n
    'value' (list): With 'from_obj', value from object\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    self = _Get_Instance(self_idx)

    element_value = None
    element_ui = None
    element_obj = None
    if line_idx == 0:
        element_value = 'target_select'
        element_ui = 'target_select_opMenu'
        element_obj = 'target_obj'
    elif line_idx == 1:
        element_value = 'cross_select'
        element_ui = 'cross_select_opMenu'
        element_obj = 'cross_grp'
    else :
        element_value = 'trail_select'
        element_ui = 'trail_select_opMenu'
        element_obj = 'trail_grp'

    if not from_obj:
        value = cmds.optionMenu( self.ui_items[element_ui], query=True, value=True )
        
        if self.ui_data[element_obj] is not None and cmds.objExists( self.ui_data[element_obj] ):
            if value == "Selectable":
                cmds.setAttr( f'{self.ui_data[element_obj]}.overrideDisplayType', 0 )
            else:
                cmds.setAttr( f'{self.ui_data[element_obj]}.overrideDisplayType', 2 )
    else:
        if self.is_expanded:
            cmds.optionMenu( self.ui_items[element_ui], edit=True, value=value )
    
    self.ui_data[element_value] = value

def _Set_Size( self_idx:int, line_idx:int, arrow_idx=None, from_obj=False, value=None, partial_empty=None ): #Set element's size
    """
    Set element's size\n
    ### Parameters:\n
    'line_idx' (int): Element index ( 0:target, 1:cross, 2:trail )\n
    'arrow_idx' (None/int): If from arrows, 0:up and 1:down\n
    'from_obj' (bool): Called from system load, only update ui and data\n
    'value' (float): With 'from_obj', value from object\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    self = _Get_Instance(self_idx)

    element_value = None
    element_ui = None
    element_obj = None
    if line_idx == 0:
        element_value = 'target_size'
        element_ui = 'target_size_decimalTextField'
        element_obj = 'target_obj'
    else:
        element_value = 'cross_size'
        element_ui = 'cross_size_decimalTextField'
        element_obj = 'cross_obj'
    
    if not from_obj:
        if arrow_idx is None:
            value = cmds.textField( self.ui_items[element_ui], query=True, text=True )
            #Check value match float format
            value, issue_str = _Check_StrToFloat( value )
            if value is None:
                cmds.textField( self.ui_items[element_ui], edit=True, text=self.ui_data[element_value] )
                if issue_str is not None:
                    cmds.error( f"[ISSUE]: {issue_str}", noContext=True )
                else:
                    return
            #Try to convert string to float, with decimal.Decimal() to make sure
            try:
                value = deci.Decimal(f'{value}')
            except Exception as exception_name:
                cmds.textField( self.ui_items[element_ui], edit=True, text=self.ui_data[element_value] )
                cmds.error( f"[ISSUE]: Invalid float value (Exception: {exception_name}, type: {type(exception_name)})", noContext=True )
        else: #If from arrows, increase or decrease
            step = 1 if line_idx == 0 else deci.Decimal('0.5')
            if arrow_idx == 0:
                value = self.ui_data[element_value] + step
            else:
                value = self.ui_data[element_value] - step
        
        # Update intField
        cmds.textField( self.ui_items[element_ui], edit=True, text=value )
        #If element_obj exists, apply size
        if self.ui_data[element_obj] is not None and cmds.objExists( self.ui_data[element_obj] ):
            float_size = float(value) if line_idx == 0 else float( value * deci.Decimal('0.01') )
            cmds.setAttr( f'{self.ui_data[element_obj]}.localScale', float_size, float_size, float_size )
    else:# From obj
        value = deci.Decimal(f'{value}')
        if line_idx == 1: #Set back cross scale to fit 1.0 in UI
            value = value * 100
        if self.is_expanded:
            cmds.textField( self.ui_items[element_ui], edit=True, text=float(value) ) #Convert back to float to remove eventual zero
    
    self.ui_data[element_value] = value

def _Set_Calcul( self_idx:int, line_idx:int, value:bool, partial_empty=None ): #Set element's calcul state
    """
    Set element's calcul state\n
    ### Parameters:\n
    'line_idx' (int): Element index ( 0:target, 1:cross, 2:trail )\n
    'value' (bool): value\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    self = _Get_Instance(self_idx)

    element_value = None
    if line_idx == 0: #Removed
        element_value = 'target_calcul'
    elif line_idx == 1:
        element_value = 'cross_calcul'
    else :
        element_value = 'trail_calcul'
    
    self.ui_data[element_value] = value

def _Set_Display( self_idx:int, line_idx:int, value:bool, from_obj=False, partial_empty=None ): #Set element's display state
    """
    Set element's display state\n
    ### Parameters:\n
    'line_idx' (int): Element index ( 0:target, 1:cross, 2:trail )\n
    'value' (bool): value\n
    'from_obj' (bool): Called from system load, only update ui and data\n
    'partial_empty' (bool): Extra 'False' argument from partial() when function call includes argument(s)
    """
    self = _Get_Instance(self_idx)

    element_value = None
    element_ui = None
    element_obj = None
    if line_idx == 0:
        element_value = 'target_display'
        element_ui = 'target_display_symbolChckBx'
        element_obj = 'target_obj'
    elif line_idx == 1:
        element_value = 'cross_display'
        element_ui = 'cross_display_symbolChckBx'
        element_obj = 'cross_grp'
    else :
        element_value = 'trail_display'
        element_ui = 'trail_display_symbolChckBx'
        element_obj = 'trail_grp'
    
    if not from_obj:
        if self.ui_data[element_obj] is not None and cmds.objExists( self.ui_data[element_obj] ):
            cmds.setAttr( f'{self.ui_data[element_obj]}.visibility', value )
    else:
        if self.is_expanded and element_ui in self.ui_items:
            cmds.symbolCheckBox( self.ui_items[element_ui], edit=True, value=value )

    self.ui_data[element_value] = value

def _Clear_Elements( self_idx:int, partial_empty=None ): #Clear duplicates of both elements
    """ Clear duplicates of both elements """
    self = _Get_Instance( self_idx )
    Clear_Element( self, self_idx, 1, True )
    Clear_Element( self, self_idx, 2, True )

def _Load_System( self, new_system:bool, camera=None ): #Load system process from just set system
    """ Load system process from just set system """
    #Reset system obj names
    to_reset = ['aim_zero_obj', 'aimmtx', 'target_obj', 'cross_grp', 'cross_obj', 'trail_grp', 'trail_obj']
    for var_name in to_reset:
        self.ui_data[var_name] = None
    
    if new_system:
        _Switch_MainBttn( self, 1 )
        return
    
    #Check if system is not None
    if self.ui_data['system'] is None:
        cmds.error( f"[ISSUE]: System name can't be 'None', please set a system name", noContext=True )
    
    #Hide
    t_value = True if cmds.getAttr( f"{self.ui_data['system']}.visibility" ) == 0 else False
    cmds.symbolCheckBox( self.ui_items['hide_symbolChckBx'], edit=True, value=t_value )
    #Rebuild
    cmds.symbolCheckBox( self.ui_items['rebuild_symbolChckBx'], edit=True, value=self.ui_data['rebuild'] )
    
    #Camera
    if camera is None:
        camera = cmds.listRelatives( self.ui_data['system'], parent=True, fullPath=True )
        if camera is None:
            cmds.warning( f"[ISSUE]: No camera found over system '{self.ui_data['system']}' !", noContext=True )
        else:
            camera = camera[0]
            if type(cmds.getAttr( f"{camera.rsplit('|',1)[1]}.nodeState" )) != list: #If there is only one camera at this name, remove fullpath before it
                camera = camera.rsplit('|',1)[1]
            _Set_Camera( self, self.SELF_IDX, True, camera )
    else:
        self.ui_data['camera'] = camera
        if self.is_expanded:
            cmds.textField( self.ui_items['camera_picker_txtField'], edit=True, text=camera )
    
    #Get system root children to load data from
    sys_children = cmds.listRelatives( self.ui_data['system'], children=True )
    target_obj = None
    aim_zero_obj = None
    cross_grp = None
    trail_grp = None
    for child in sys_children:
        if child.endswith('_target_loc'):
            target_obj = child
            continue
        elif child.endswith('_aim'):
            aim_zero_obj = cmds.listRelatives( child, children=True )[0]
            continue
        elif child.endswith('_cross_grp'):
            cross_grp = child
            continue
        elif child.endswith('_trail_grp'):
            trail_grp = child
            continue

    #Target
    if target_obj is None:
        cmds.warning( f"[ISSUE]: Couldn't find target object under system!", noContext=True )
    else:
        self.ui_data['target_obj'] = target_obj
        # Color
        _Set_Color( self.SELF_IDX, 0, True, cmds.getAttr( f'{target_obj}.overrideColorRGB' ) )
        # Selectable
        t_value = "Selectable" if cmds.getAttr( f'{target_obj}.overrideDisplayType' ) == 0 else "Non selectable"
        _Set_Selectable( self.SELF_IDX, 0, True, t_value )
        # Size
        _Set_Size( self.SELF_IDX, 0, None, True, cmds.getAttr( f'{target_obj}.localScaleX' ) )
        # Display
        t_value = True if cmds.getAttr( f'{target_obj}.visibility' ) == 1 else False
        _Set_Display( self.SELF_IDX, 0, t_value, True )
        
    #Aim
    if aim_zero_obj is None:
        cmds.warning( f"[ISSUE]: Couldn't find aim_zero object under system!", noContext=True )
    else:
        cam_dist = deci.Decimal(f"{cmds.getAttr( f'{aim_zero_obj}.translateX' )}")
        self.ui_data['aim_dist'] = cam_dist
        if self.is_expanded:
            cmds.textField( self.ui_items['aim_dist_textField'], edit=True, text=cam_dist )
        self.ui_data['aim_zero_obj'] = aim_zero_obj
    t_value = cmds.listRelatives( aim_zero_obj, parent=True )
    if t_value is None:
        cmds.warning( f"[ISSUE]: Couldn't find system's aim matrix node!", noContext=True )
    t_value2 = cmds.connectionInfo( f'{t_value[0]}.offsetParentMatrix', sourceFromDestination=True )
    if t_value2 == '':
        cmds.warning( f"[ISSUE]: System's aim matrix seems disconnected from aim object {t_value[0]}.offsetParentMatrix and couldn't be loaded!", noContext=True )
    self.ui_data['aimmtx'] = t_value2.rsplit('.',1)[0]

    #Cross
    if cross_grp is None:
        cmds.warning( f"[ISSUE]: Couldn't find cross_grp under system!", noContext=True )
    else:
        self.ui_data['cross_grp'] = cross_grp
        cross_obj = cross_grp.replace('_grp','_ref',1)
        if not cmds.objExists( cross_obj ):
            cmds.warning( f"[ISSUE]: Couldn't find cross_obj '{cross_obj}' under system!", noContext=True )
        self.ui_data['cross_obj'] = cross_obj
        # Color
        _Set_Color( self.SELF_IDX, 1, True, cmds.getAttr( f'{cross_grp}.overrideColorRGB' ) )
        # Selectable
        t_value = "Selectable" if cmds.getAttr( f'{cross_grp}.overrideDisplayType' ) == 0 else "Non selectable"
        _Set_Selectable( self.SELF_IDX, 1, True, t_value )
        # Size
        _Set_Size( self.SELF_IDX, 1, None, True, cmds.getAttr( f'{cross_obj}.localScaleX' ) )
        # Display
        t_value = True if cmds.getAttr( f'{cross_grp}.visibility' ) == 1 else False
        _Set_Display( self.SELF_IDX, 1, t_value, True )

    #Trail
    if trail_grp is None:
        cmds.warning( f"[ISSUE]: Couldn't find trail_grp under system!", noContext=True )
    else:
        self.ui_data['trail_grp'] = trail_grp
        trail_obj = trail_grp.replace('_grp','_ref',1)
        if not cmds.objExists( cross_obj ):
            cmds.warning( f"[ISSUE]: Couldn't find trail_obj '{trail_obj}' under system!", noContext=True )
        self.ui_data['trail_obj'] = trail_obj
        # Color
        _Set_Color( self.SELF_IDX, 2, True, cmds.getAttr( f'{trail_grp}.overrideColorRGB' ) )
        # Selectable
        t_value = "Selectable" if cmds.getAttr( f'{trail_grp}.overrideDisplayType' ) == 0 else "Non selectable"
        _Set_Selectable( self.SELF_IDX, 2, True, t_value )
        # Display
        t_value = True if cmds.getAttr( f'{trail_grp}.visibility' ) == 1 else False
        _Set_Display( self.SELF_IDX, 2, t_value, True )
        
    #Make sure the button is on calculate
    _Switch_MainBttn( self, 0 )

def _Calculate_All_Callback( self_idx:int,    drgCllBck_drgCtrl=None, drgCllBck_x=None, drgCllBck_y=None, drgCllBck_mod=None ): #Call Calculate_All() from UI
    """ Call Calculate_All() from UI """
    if drgCllBck_mod == 2:
        Calculate_All()
    elif drgCllBck_mod == 3:
        Calculate_All( (self_idx,) )
#endregion - * UI/Features *

#region - * Window *
def _Build_Win_Expanded( self, self_idx:int ): #Build expanded window
    """ Build expanded window """
    if self is None:
        self = _Get_Instance( self_idx )
    SELF_IDX = self.SELF_IDX
    main_formLyt = cmds.formLayout()
    main_clmnLyt = cmds.columnLayout(
        adjustableColumn=True,
        parent=main_formLyt
    )
    
    #region - System
    sys_rowLyt = cmds.rowLayout(
        height=50,
        numberOfColumns=5,
        rowAttach=( (1, 'bottom', 0), (2, 'bottom', 0), (3, 'bottom', 0), (4, 'bottom', 0), (5, 'bottom', 0) ),
        parent=main_clmnLyt
    )
    #System
    cmds.text(
        height=40,
        label="<font size=7><i><b>SYSTEM</b></i></font>", align='left',
        parent=sys_rowLyt
    )
    cmds.separator( height=40, width=10, style='none', parent=sys_rowLyt )
    sys_rowClmnLyt = cmds.rowColumnLayout(
        height=40,
        numberOfRows=1,
        rowAttach=[1, 'top', 2],
        parent=sys_rowLyt
    )
    sys_value = self.ui_data['system'] if self.ui_data['system'] is not None else 'None'
    self.ui_items['sys_picker_txtField'], self.ui_items['sys_picker_symbolBttn'] = _Build_PickerBttn( #Picker
        sys_rowClmnLyt, 32,
        (
            200, sys_value, True, partial(_Set_System, None, SELF_IDX, False, None),
            "System's name\n\n[Middle mouse]: Select system root",
            "System's name    [Middle mouse]: Select system root",
            self.THEME['sys_pickField_back'], partial(_Select_Callback, SELF_IDX, 0)
        ),
        8,
        (
            partial(_Pick_Init, SELF_IDX, 1, _Pick_System_Done, 0, ('transform',), True, False, False),
            "Pick system\n\nShould find system from system root,\ncamera and target element",
            "Pick system  -  Should find system from system root, camera and target element",
            self.THEME['sys_pick_back_off']
        )
    )
    cmds.separator( height=40, width=60, style='none', parent=sys_rowClmnLyt )
    
    #Hide
    sys_exists = True if self.ui_data['system'] is not None and cmds.objExists( self.ui_data['system'] ) else False
    sys_hide_state = False
    if sys_exists and cmds.getAttr( f"{self.ui_data['system']}.visibility" ) == 0:
        sys_hide_state = True
    self.ui_items['hide_symbolChckBx'] = cmds.symbolCheckBox(
        height=32, width=32,
        onImage='Bool_Hidden.png', offImage='eye.png', highlightColor=self.THEME['sys_symbolChckBx_high_back'], value=sys_hide_state,
        onCommand=partial(_Set_Hide, SELF_IDX, True), offCommand=partial(_Set_Hide, SELF_IDX, False),
        annotation="Toggle system's visibility", statusBarMessage="Toggle system's visibility",
        backgroundColor=self.THEME['sys_bttn_back'],
        parent=sys_rowClmnLyt
    )
    cmds.separator( height=40, width=25, style='none', parent=sys_rowClmnLyt )
    
    #Rebuild
    self.ui_items['rebuild_symbolChckBx'] = cmds.symbolCheckBox(
        height=32, width=32,
        onImage='autoKeyframe.png', offImage='lock.png', highlightColor=self.THEME['sys_bttn_back'], value=self.ui_data['rebuild'],
        onCommand=partial(_Set_Rebuild, SELF_IDX, True, False), offCommand=partial(_Set_Rebuild, SELF_IDX, False, False),
        annotation="Toggle elements rebuild on calculate\n\nMay leave garbage but prevent unecessary duplicating",
        statusBarMessage="Toggle elements rebuild on calculate  -  May leave garbage but prevent unecessary duplicating",
        backgroundColor=self.THEME['sys_symbolChckBx_high_back'],
        parent=sys_rowClmnLyt
    )
    cmds.separator( height=40, width=25, style='none', parent=sys_rowClmnLyt )

    #Scale fix
    self.ui_items['scalefix_symbolChckBx'] = cmds.symbolCheckBox(
        height=32, width=32,
        onImage='Bool_CutOut.png', offImage='ghostingObjectTypeAll.png', highlightColor=self.THEME['sys_symbolChckBx_high_back'], value=self.ui_data['scale_fix'],
        onCommand=partial(_Set_Scale_Fix, SELF_IDX, True), offCommand=partial(_Set_Scale_Fix, SELF_IDX, False),
        annotation="Compensate animated scale on camera during calcul\nto keep crosses at a constant size in camera\n( Disabled if using pool )\n\nCaution! This may cause huge objects",
        statusBarMessage="Compensate animated scale on camera during calcul to keep crosses at a constant size ( Disabled if using pool )  -  Caution! This may cause huge objects",
        backgroundColor=self.THEME['sys_bttn_back'],
        parent=sys_rowClmnLyt
    )
    cmds.separator( height=40, width=25, style='none', parent=sys_rowClmnLyt )
    
    #Delete
    cmds.symbolButton(
        height=32, width=32,
        image='delete.png',
        command=partial(Delete_System, None, SELF_IDX),
        annotation="Delete system", statusBarMessage="Delete system",
        backgroundColor=self.THEME['sys_deleteBttn_back'],
        parent=sys_rowClmnLyt
    )
    
    #Compact
    cmds.separator( height=40, width=117, style='none', parent=sys_rowLyt )
    cmds.symbolButton(
        height=50, width=50,
        image='polyFlip.png',
        command=partial(Build_Window, None, self_idx, False, False),
        annotation="Compact window", statusBarMessage="Compact window",
        backgroundColor=self.THEME['sys_bttn_back'],
        parent=sys_rowLyt
    )
    #endregion - System
    cmds.separator( height=20, style='none', parent=main_clmnLyt )
    
    #region - Sys extra row 1
    sys_extra1_rowLyt = cmds.rowLayout(
        height=40,
        numberOfColumns=16,
        parent=main_clmnLyt
    )
    cmds.separator( height=30, width=5, style='none', parent=sys_extra1_rowLyt )
    
    #Camera
    cmds.text(
        height=30,
        label='<font size=5><b>CAMERA</b></font>',
        parent=sys_extra1_rowLyt
    )
    cmds.separator( height=30, width=3, style='none', parent=sys_extra1_rowLyt )
    camera_value = self.ui_data['camera'] if self.ui_data['camera'] is not None else 'None'
    self.ui_items['camera_picker_txtField'], self.ui_items['camera_picker_symbolBttn'] = _Build_PickerBttn( #Picker
        sys_extra1_rowLyt, 30,
        (
            150, camera_value, True, partial(_Set_Camera, None, SELF_IDX, False, None),
            "System's camera\n\n[Middle mouse]: Select camera",
            "System's camera    [Middle mouse]: Select camera",
            self.THEME['pickField_back'], partial(_Select_Callback, SELF_IDX, 1)
        ),
        3,
        (
            partial(_Pick_Init, SELF_IDX, 1, _Pick_Camera_Done, 1, ('transform',), True, False, False),
            "Pick system's camera\n\n[Middle mouse]: If no camera already selected,\nget active view's camera",
            "Pick system's camera    [Middle mouse]: If no camera already selected, get active view's camera",
            self.THEME['pick_back_off'],
            None,
            partial(_Pick_Init_Callback, SELF_IDX, 1, _Pick_Camera_Done, 2, ('transform',), True, False, False)
        )
    )
    cmds.separator( height=30, width=60, style='none', parent=sys_extra1_rowLyt )
    
    #Range
    cmds.text(
        height=30,
        label='<font size=5><b>RANGE</b></font>',
        parent=sys_extra1_rowLyt
    )
    cmds.separator( height=30, width=3, style='none', parent=sys_extra1_rowLyt )
    range_opMenu = cmds.optionMenu(
        height=30, width=150,
        maxVisibleItems=3, changeCommand=partial(_Set_Range, SELF_IDX),
        annotation="Range in which to calulate the motion trail", statusBarMessage="Range in which to calulate the motion trail",
        backgroundColor=self.THEME['drpdwn_back'],
        parent=sys_extra1_rowLyt
    )
    self.ui_items['range_opMenu'] = range_opMenu
    cmds.menuItem( label="Slider", parent=range_opMenu )
    cmds.menuItem( label="Anim", parent=range_opMenu )
    cmds.menuItem( label="Custom", parent=range_opMenu )
    cmds.optionMenu( range_opMenu, edit=True, value=self.ui_data['range'] )
    cmds.separator( height=30, width=16, style='none', parent=sys_extra1_rowLyt )
    
    #Custom range
    cstm_range_rowLyt = cmds.rowLayout(
        height=31,
        numberOfColumns=5,
        parent=sys_extra1_rowLyt
    )
    self.ui_items['cstm_range_rowLyt'] = cstm_range_rowLyt
    self.ui_items['cstm_range_s_textField'] = _Build_DecimalTextField(
        cstm_range_rowLyt, 30,
        ( 50, True, partial(_Set_CstmRange, SELF_IDX, 0, None), self.ui_data['cstm_range'][0], "Start frame", "Start frame" ),
        None,
        ( 12, 0, 2, partial(_Set_CstmRange, SELF_IDX, 0, 0), partial(_Set_CstmRange, SELF_IDX, 0, 1) ),
        self.THEME['bttn_back']
    )
    cmds.separator( height=30, width=8, style='none', parent=cstm_range_rowLyt )
    self.ui_items['cstm_range_e_textField'] = _Build_DecimalTextField(
        cstm_range_rowLyt, 30,
        ( 50, True, partial(_Set_CstmRange, SELF_IDX, 1, None), self.ui_data['cstm_range'][1], "End frame", "End frame" ),
        None,
        ( 12, 0, 2, partial(_Set_CstmRange, SELF_IDX, 1, 0), partial(_Set_CstmRange, SELF_IDX, 1, 1) ),
        self.THEME['bttn_back']
    )
    _Update_CstmRangeUI( self )
    #endregion - Sys extra row 1
    cmds.separator( height=5, style='none', parent=main_clmnLyt )
    
    #region - Sys extra row 2
    sys_extra2_rowLyt = cmds.rowLayout(
        height=40,
        numberOfColumns=16,
        parent=main_clmnLyt
    )
    cmds.separator( height=30, width=5, style='none', parent=sys_extra2_rowLyt )
    
    #Step
    cmds.text(
        height=30,
        label='<font size=5><b>STEP</b></font>',
        parent=sys_extra2_rowLyt
    )
    cmds.separator( height=30, width=3, style='none', parent=sys_extra2_rowLyt )
    self.ui_items['step_textField'] = _Build_DecimalTextField(
        sys_extra2_rowLyt, 30,
        ( 50, True, partial(_Set_Step, SELF_IDX, None), self.ui_data['step'], "Number of frames between each cross", "Number of frames between each cross" ),
        None,
        ( 12, 0, 2, partial(_Set_Step, SELF_IDX, 0), partial(_Set_Step, SELF_IDX, 1) ),
        self.THEME['bttn_back']
    )
    
    cmds.separator( height=30, width=213, style='none', parent=sys_extra2_rowLyt )
    
    #Pool
    cmds.text(
        height=30,
        label='<font size=5><b>POOL</b></font>',
        parent=sys_extra2_rowLyt
    )
    cmds.separator( height=30, width=3, style='none', parent=sys_extra2_rowLyt )
    self.ui_items['pool_intField'] = _Build_IntField(
        sys_extra2_rowLyt, 30,
        ( 100, True, partial(_Set_Pool, SELF_IDX, None), self.ui_data['pool'], 0, None, "Maximum number of crosses and trails to create.\nIf reached, oldest elements will be reused\n\n[ Set to 0 to disable ]", "Maximum number of crosses and trails to create. If reached, oldest elements will be reused    [ Set to 0 to disable ]" ),
        None,
        ( 12, 0, 2, partial(_Set_Pool, SELF_IDX, 0), partial(_Set_Pool, SELF_IDX, 1) ),
        self.THEME['bttn_back']
    )

    cmds.separator( height=30, width=177, style='none', parent=sys_extra2_rowLyt )
    
    #Camera distance
    cmds.text(
        height=30,
        label=f"<font size=5><font color={self.THEME['side_param_Txt']}><b>DIST</b></font color></font>",
        parent=sys_extra2_rowLyt
    )
    cmds.separator( height=30, width=3, style='none', parent=sys_extra2_rowLyt )
    self.ui_items['aim_dist_textField'] = _Build_DecimalTextField(
        sys_extra2_rowLyt, 30,
        ( 40, True, partial(_Set_Cam_Dist, SELF_IDX, None), self.ui_data['aim_dist'], "Cross and trail elements' distance\nfrom camera\n\nCaution! Increasing distance will also\nincrease their size in the scene", "Cross and trail elements' distance from camera  -  Caution! Increasing distance will also increase their size in the scene" ),
        None,
        ( 12, 0, 2, partial(_Set_Cam_Dist, SELF_IDX, 0), partial(_Set_Cam_Dist, SELF_IDX, 1) ),
        self.THEME['bttn_back']
    )
    #endregion - Sys extra row 2
    cmds.separator( height=5, style='none', parent=main_clmnLyt )

    #region - Sub items options
    sub_clmnLyt = cmds.columnLayout(
        height=190,
        columnOffset=('both',15),
        adjustableColumn=True,
        backgroundColor=self.THEME['sub_back'],
        parent=main_clmnLyt
    )
    cmds.separator( height=13, style='none', parent=sub_clmnLyt )

    #Target
    self.ui_items['target_color_bttn'], self.ui_items['target_select_opMenu'], self.ui_items['target_size_decimalTextField'], empty, self.ui_items['target_display_symbolChckBx'] = _Build_SubLine(
        self, sub_clmnLyt,
        ( 'polyAxis.png', partial(_Select_Callback, SELF_IDX, 2), partial(_Select_Callback, SELF_IDX, 2), "Target element\n\n[Middle mouse]: Select target", "Target element    [Middle mouse]: Select target" ),
        ( partial(_Set_Color, SELF_IDX, 0, False, None), self.ui_data['target_color'] ),
        ( partial(_Set_Selectable, SELF_IDX, 0, False, None), self.ui_data['target_select'] ),
        ( partial(_Set_Size, SELF_IDX, 0, None, False, None), partial(_Set_Size, SELF_IDX, 0, 0, False, None), partial(_Set_Size, SELF_IDX, 0, 1, False, None), self.ui_data['target_size'] ),
        None,
        ( partial(_Set_Display, SELF_IDX, 0, True, False), partial(_Set_Display, SELF_IDX, 0, False, False), self.ui_data['target_display'] ),
        None
    )
    cmds.separator( height=18, style='none', parent=sub_clmnLyt )

    #Cross
    self.ui_items['cross_color_bttn'], self.ui_items['cross_select_opMenu'], self.ui_items['cross_size_decimalTextField'], self.ui_items['cross_calcul_symbolChckBx'], self.ui_items['cross_display_symbolChckBx'] = _Build_SubLine(
        self, sub_clmnLyt,
        ( 'ts-head3.png', None, None, "Cross element", "Cross element" ),
        ( partial(_Set_Color, SELF_IDX, 1, False, None), self.ui_data['cross_color'] ),
        ( partial(_Set_Selectable, SELF_IDX, 1, False, None), self.ui_data['cross_select'] ),
        ( partial(_Set_Size, SELF_IDX, 1, None, False, None), partial(_Set_Size, SELF_IDX, 1, 0, False, None), partial(_Set_Size, SELF_IDX, 1, 1, False, None), self.ui_data['cross_size'] ),
        ( partial(_Set_Calcul, SELF_IDX, 1, True), partial(_Set_Calcul, SELF_IDX, 1, False), self.ui_data['cross_calcul'] ),
        ( partial(_Set_Display, SELF_IDX, 1, True, False), partial(_Set_Display, SELF_IDX, 1, False, False), self.ui_data['cross_display'] ),
        partial(Clear_Element, None, SELF_IDX, 1, False)
    )
    cmds.separator( height=18, style='none', parent=sub_clmnLyt )

    #Trail
    self.ui_items['trail_color_bttn'], self.ui_items['trail_select_opMenu'], empty, self.ui_items['trail_calcul_symbolChckBx'], self.ui_items['trail_display_symbolChckBx'] = _Build_SubLine(
        self, sub_clmnLyt,
        ( 'selectEdgePath.png', None, None, "Trail element", "Trail element" ),
        ( partial(_Set_Color, SELF_IDX, 2, False, None), self.ui_data['trail_color'] ),
        ( partial(_Set_Selectable, SELF_IDX, 2, False, None), self.ui_data['trail_select'] ),
        None,
        ( partial(_Set_Calcul, SELF_IDX, 2, True), partial(_Set_Calcul, SELF_IDX, 2, False), self.ui_data['trail_calcul'] ),
        ( partial(_Set_Display, SELF_IDX, 2, True, False), partial(_Set_Display, SELF_IDX, 2, False, False), self.ui_data['trail_display'] ),
        partial(Clear_Element, None, SELF_IDX, 2, False)
    )
    #endregion - Sub item options
    cmds.separator( height=8, style='none', parent=main_clmnLyt )
    
    #region - Calculate
    #Calculate
    calc_clmnLyt = cmds.columnLayout(
        height=42,
        columnAttach=('left', (self.WIN_SIZE_WH[0]*0.5)-110),
        parent=main_clmnLyt
    )
    calculate_bttn_state = True if sys_exists else False
    self.ui_items['calculate_symbolBttn'] = cmds.symbolButton(
        height=40, width=200,
        image='out_timeEditorAnimSource.png', command=partial(Calculate, None, SELF_IDX), visible=calculate_bttn_state, dragCallback=partial(_Calculate_All_Callback, self_idx),
        annotation="Calculate motion trail\n\n[Ctrl+Middle mouse]: Calculate all instances\n[Ctrl+Shift+Middle mouse]: Calculate all instances\nstarting by current window's index",
        statusBarMessage="Calculate motion trail    [Ctrl+Middle mouse]: Calculate all instances - [Ctrl+Shift+Middle mouse]: Calculate all instances starting by current window's index",
        backgroundColor=self.THEME['bttn_back'],
        parent=calc_clmnLyt
    )
    #Build system
    calculate_bttn_state = False if calculate_bttn_state else True
    self.ui_items['buildsys_symbolBttn'] = cmds.symbolButton(
        height=40, width=200,
        image='teCreateClip.png', command=partial(Build_System, None, SELF_IDX), visible=calculate_bttn_state,
        annotation="Create motion trail system", statusBarMessage="Create motion trail system",
        backgroundColor=self.THEME['build_bttn_back'],
        parent=calc_clmnLyt
    )
    #endregion - Calculate

    #region - End setup
    cmds.formLayout(
        main_formLyt, edit=True,
        attachForm=(
            (main_clmnLyt, 'top', 10), (main_clmnLyt, 'left', 10), (main_clmnLyt, 'right', 10), (main_clmnLyt, 'bottom', 11)
        )
    )
    cmds.showWindow()
    #endregion - End setup

def _Build_Win_Compact( self, self_idx:int ): #Build compact window
    """ Build compact window """
    if self is None:
        self = _Get_Instance( self_idx )
    SELF_IDX = self.SELF_IDX
    main_formLyt = cmds.formLayout()
    main_clmnLyt = cmds.columnLayout(
        adjustableColumn=True,
        parent=main_formLyt
    )
    
    #region - System
    sys_rowLyt = cmds.rowLayout(
        height=60,
        numberOfColumns=3,
        rowAttach=( (1, 'bottom', 0), (2, 'bottom', 0), (3, 'top', 0) ),
        parent=main_clmnLyt
    )
    #System
    cmds.text(
        height=40,
        label="<font size=7><i><b>SYSTEM</b></i></font>", align='left',
        parent=sys_rowLyt
    )
    #Expand
    cmds.separator( height=40, width=76, style='none', parent=sys_rowLyt )
    cmds.symbolButton(
        height=50, width=50,
        image='radialField.svg',
        command=partial(Build_Window, None, self_idx, True),
        annotation="Expand window", statusBarMessage="Expand window",
        backgroundColor=self.THEME['sys_bttn_back'],
        parent=sys_rowLyt
    )
    cmds.separator( height=5, style='none', parent=main_clmnLyt )

    #System picker
    sys_rowClmnLyt = cmds.rowColumnLayout(
        height=33,
        numberOfRows=1,
        rowAttach=[1, 'top', 0],
        parent=main_clmnLyt
    )
    sys_value = self.ui_data['system'] if self.ui_data['system'] is not None else 'None'
    self.ui_items['sys_picker_txtField'], self.ui_items['sys_picker_symbolBttn'] = _Build_PickerBttn( #Picker
        sys_rowClmnLyt, 32,
        (
            186, sys_value, True, partial(_Set_System, None, SELF_IDX, False, None),
            "System's name\n\n[Middle mouse]: Select system root",
            "System's name    [Middle mouse]: Select system root",
            self.THEME['sys_pickField_back'], partial(_Select_Callback, SELF_IDX, 0)
        ),
        8,
        (
            partial(_Pick_Init, SELF_IDX, 1, _Pick_System_Done, 0, ('transform',), True, False, False),
            "Pick system\n\nShould find system from system root,\ncamera and target element",
            "Pick system  -  Should find system from system root, camera and target element",
            self.THEME['sys_pick_back_off']
        )
    )
    cmds.separator( height=13, style='none', parent=main_clmnLyt )

    sys2_rowClmnLyt = cmds.rowColumnLayout(
        height=33,
        numberOfRows=1,
        rowAttach=[1, 'top', 0],
        parent=main_clmnLyt
    )
    #Target
    cmds.symbolButton(
        height=32, width=32,
        image='polyAxis.png',
        command=partial(_Select_Callback, SELF_IDX, 2), dragCallback=partial(_Select_Callback, SELF_IDX, 2),
        annotation="Select target element", statusBarMessage="Select target element",
        backgroundColor=self.THEME['sys_bttn_back'],
        parent=sys2_rowClmnLyt
    )
    cmds.separator( height=40, width=38, style='none', parent=sys2_rowClmnLyt )
    
    #Hide
    sys_exists = True if self.ui_data['system'] is not None and cmds.objExists( self.ui_data['system'] ) else False
    sys_hide_state = False
    if sys_exists and cmds.getAttr( f"{self.ui_data['system']}.visibility" ) == 0:
        sys_hide_state = True
    self.ui_items['hide_symbolChckBx'] = cmds.symbolCheckBox(
        height=32, width=32,
        onImage='Bool_Hidden.png', offImage='eye.png', highlightColor=self.THEME['sys_symbolChckBx_high_back'], value=sys_hide_state,
        onCommand=partial(_Set_Hide, SELF_IDX, True), offCommand=partial(_Set_Hide, SELF_IDX, False),
        annotation="Toggle system's visibility", statusBarMessage="Toggle system's visibility",
        backgroundColor=self.THEME['sys_bttn_back'],
        parent=sys2_rowClmnLyt
    )
    cmds.separator( height=40, width=27, style='none', parent=sys2_rowClmnLyt )
    
    #Rebuild
    self.ui_items['rebuild_symbolChckBx'] = cmds.symbolCheckBox(
        height=32, width=32,
        onImage='autoKeyframe.png', offImage='lock.png', highlightColor=self.THEME['sys_bttn_back'], value=self.ui_data['rebuild'],
        onCommand=partial(_Set_Rebuild, SELF_IDX, True, False), offCommand=partial(_Set_Rebuild, SELF_IDX, False, False),
        annotation="Toggle elements rebuild on calculate\n\nMay leave garbage but prevent unecessary duplicating", statusBarMessage="Toggle elements rebuild on calculate  -  May leave garbage but prevent unecessary duplicating",
        backgroundColor=self.THEME['sys_symbolChckBx_high_back'],
        parent=sys2_rowClmnLyt
    )
    cmds.separator( height=40, width=27, style='none', parent=sys2_rowClmnLyt )
    
    #Clear elements
    cmds.symbolButton(
        height=32, width=32,
        image='delete.png',
        command=partial(_Clear_Elements, SELF_IDX),
        annotation="Clear elements", statusBarMessage="Clear elements",
        backgroundColor=self.THEME['sys_bttn_back'],
        parent=sys2_rowClmnLyt
    )
    #endregion - System
    cmds.separator( height=13, style='none', parent=main_clmnLyt )
    
    #region - Sys extra row 1
    #Range
    range_rowLyt = cmds.rowLayout(
        height=40,
        numberOfColumns=3,
        parent=main_clmnLyt
    )
    cmds.text(
        height=30,
        label='<font size=5><b>RANGE</b></font>',
        parent=range_rowLyt
    )
    cmds.separator( height=30, width=9, style='none', parent=range_rowLyt )
    range_opMenu = cmds.optionMenu(
        height=30, width=150,
        maxVisibleItems=3, changeCommand=partial(_Set_Range, SELF_IDX),
        annotation="Range in which to calulate the motion trail", statusBarMessage="Range in which to calulate the motion trail",
        backgroundColor=self.THEME['drpdwn_back'],
        parent=range_rowLyt
    )
    self.ui_items['range_opMenu'] = range_opMenu
    cmds.menuItem( label="Slider", parent=range_opMenu )
    cmds.menuItem( label="Anim", parent=range_opMenu )
    cmds.menuItem( label="Custom", parent=range_opMenu )
    cmds.optionMenu( range_opMenu, edit=True, value=self.ui_data['range'] )
    
    #Custom range
    cstm_range_clmnLyt = cmds.rowLayout(
        height=31,
        numberOfColumns=5, columnAttach=(1, 'left', 71),
        parent=main_clmnLyt
    )
    self.ui_items['cstm_range_rowLyt'] = cstm_range_clmnLyt
    self.ui_items['cstm_range_s_textField'] = _Build_DecimalTextField(
        cstm_range_clmnLyt, 30,
        ( 50, True, partial(_Set_CstmRange, SELF_IDX, 0, None), self.ui_data['cstm_range'][0], "Start frame", "Start frame" ),
        None,
        ( 12, 0, 2, partial(_Set_CstmRange, SELF_IDX, 0, 0), partial(_Set_CstmRange, SELF_IDX, 0, 1) ),
        self.THEME['bttn_back']
    )
    cmds.separator( height=30, width=8, style='none', parent=cstm_range_clmnLyt )
    self.ui_items['cstm_range_e_textField'] = _Build_DecimalTextField(
        cstm_range_clmnLyt, 30,
        ( 50, True, partial(_Set_CstmRange, SELF_IDX, 1, None), self.ui_data['cstm_range'][1], "End frame", "End frame" ),
        None,
        ( 12, 0, 2, partial(_Set_CstmRange, SELF_IDX, 1, 0), partial(_Set_CstmRange, SELF_IDX, 1, 1) ),
        self.THEME['bttn_back']
    )
    _Update_CstmRangeUI( self )
    #endregion - Sys extra row 1
    cmds.separator( height=8, style='none', parent=main_clmnLyt )

    #region - Calculate
    #Calculate
    calc_clmnLyt = cmds.columnLayout(
        height=42,
        columnAttach=('left', (self.WIN_SIZE_WH[0]*0.5)-110),
        parent=main_clmnLyt
    )
    calculate_bttn_state = True if sys_exists else False
    self.ui_items['calculate_symbolBttn'] = cmds.symbolButton(
        height=40, width=200,
        image='out_timeEditorAnimSource.png', command=partial(Calculate, None, SELF_IDX), visible=calculate_bttn_state, dragCallback=partial(_Calculate_All_Callback, self_idx),
        annotation="Calculate motion trail\n\n[Ctrl+Middle mouse]: Calculate all instances\n[Ctrl+Shift+Middle mouse]: Calculate all instances\nstarting by current window's index",
        statusBarMessage="Calculate motion trail    [Ctrl+Middle mouse]: Calculate all instances - [Ctrl+Shift+Middle mouse]: Calculate all instances starting by current window's index",
        backgroundColor=self.THEME['bttn_back'],
        parent=calc_clmnLyt
    )
    #Build system
    calculate_bttn_state = False if calculate_bttn_state else True
    self.ui_items['buildsys_symbolBttn'] = cmds.symbolButton(
        height=40, width=200,
        image='teCreateClip.png', command=partial(Build_System, None, SELF_IDX), visible=calculate_bttn_state,
        annotation="Create motion trail system", statusBarMessage="Create motion trail system",
        backgroundColor=self.THEME['build_bttn_back'],
        parent=calc_clmnLyt
    )
    #endregion - Calculate

    #region - End setup
    cmds.formLayout(
        main_formLyt, edit=True,
        attachForm=(
            (main_clmnLyt, 'top', 10), (main_clmnLyt, 'left', 10), (main_clmnLyt, 'right', 10), (main_clmnLyt, 'bottom', 21)
        )
    )
    cmds.showWindow()
    #endregion - End setup
#endregion - * Window *

#region - * Public *
def Load( multi_windows=True, keep_win_pref=False, expanded=True ): #Load/Create Local_MotionTrail instance
    """
    Load/Create Local_MotionTrail instance\n
    ### Parameters:\n
    'multi_windows' (bool): Create a new window instance of the tool\n
    'keep_win_pref' (bool): Keep window preferences as position or size\n
        Note: If multiple windows, each one will have it's own window preferences saved following their incremented name\n
    'expanded' (bool): Build expanded or contracted window by default
    """
    if not multi_windows and global_win_count != 0: #If not multi_windows and instance 0 exists, replace it's window closeCommand to prevent executing Close() after creating the new instance object
        _Clear_WindowClose( 0, "[INFO]: Reloading instance index 0" )
    new_instance = Local_MotionTrail_Window( multi_windows, keep_win_pref, expanded )

def Build_Window( self, self_idx:int, expanded:bool, init=False, partial_empty=None ): #Build instance window
    """
    Build instance window\n
    ### Parameters:\n
    'self' (None/Local_MotionTrail_Window): class object. If None, autofilled with the help of 'self_idx'\n
    'self_idx' (int): class object index in global_win_instances\n
    'expanded' (bool): If True, rebuild as expanded. If False, rebduild as contracted\n
    'init' (bool): If false, recover window's position\n
    'partial_empty' (bool): (To ignore) Extra 'False' argument from partial() when function call includes argument(s)
    """
    if self is None:
        self = _Get_Instance( self_idx )
    
    if not init:
        _Clear_WindowClose( self_idx, 0 )
    
    #Store previous position
    old_pos = None if init else cmds.window( self.WIN_NAME, query=True, topLeftCorner=True )
    #Update size
    self.WIN_SIZE_WH = self.WIN_SIZE_SETS[0] if expanded else self.WIN_SIZE_SETS[1]
    
    #region - init UI
    #Close old window at same name if exists and clear or edit windowPref if has to
    if cmds.window( self.WIN_NAME, exists=True ):
        cmds.deleteUI( self.WIN_NAME, window=True )
    if not self.WIN_KEEP_PREF: #Asked to not keep windowPref, clear it if it exists
        if cmds.windowPref( self.WIN_NAME, exists=True ):
            cmds.windowPref( self.WIN_NAME, remove=True )
    elif not expanded: #Compact and windowPref to keep and exists, change widthHeight to match compact widthHeight
        if cmds.windowPref( self.WIN_NAME, exists=True ):
            cmds.windowPref( self.WIN_NAME, edit=True, widthHeight=self.WIN_SIZE_WH )
    
    #Create new window
    self.WINDOW = cmds.window(
        self.WIN_NAME,
        title=self.WIN_TITLE,
        widthHeight=self.WIN_SIZE_WH,
        sizeable=self.WIN_SIZEABLE,
        closeCommand=partial(Close, self_idx), ##f"_Pick_Cancel(None,{self_idx})",
        backgroundColor=self.THEME['main_back']
    )
    #endregion - init UI

    #Reapply previous position
    if not init:
        cmds.window( self.WIN_NAME, edit=True, topLeftCorner=old_pos )
    self.is_expanded = expanded
    
    if expanded:
        _Build_Win_Expanded( self, self_idx )
    else:
        _Build_Win_Compact( self, self_idx )

def Build_System( self, self_idx:int, partial_empty=None ): #Build system assuming self.ui_data values are correct
    """
    Build system assuming self.ui_data values are correct\n
    ### Parameters:\n
    'self' (None/Local_MotionTrail_Window): class object. If None, autofilled with the help of 'self_idx'\n
    'self_idx' (int): class object index in global_win_instances\n
    'partial_empty' (bool): (To ignore) Extra 'False' argument from partial() when function call includes argument(s)
    """
    if self is None:
        self = _Get_Instance( self_idx )
    
    # Check variables
    if self.ui_data['system'] is None:
        cmds.error( f"[ISSUE]: System name can't be 'None', please set a system name", noContext=True )
    if cmds.objExists( self.ui_data['system'] ):
        cmds.error( f"[ISSUE]: An object named '{self.ui_data['system']}' already exists!", noContext=True )
    if self.ui_data['camera'] is None:
        cmds.error( f"[ISSUE]: No camera set, please set a camera", noContext=True )
    if not cmds.objExists( self.ui_data['camera'] ):
        cmds.error( f"[ISSUE]: No object '{self.ui_data['camera']}' found!", noContext=True )
    # Check variables

    #System root
    system_obj = cmds.createNode( 'transform', name=self.ui_data['system'], parent=self.ui_data['camera'], skipSelect=True )
    if self.ui_data['system'] != system_obj:
        old_name = self.ui_data['system']
        self.ui_data['system'] = system_obj
        cmds.textField( self.ui_items['sys_picker_txtField'], edit=True, text=system_obj )
        cmds.warning( f"[ISSUE]: '{old_name}' wasn't a valid object name to Maya sorry, the system name is now '{system_obj}'", noContext=True )
    _Lock_Transf( system_obj )
    
    #Target
    target_obj = _Create_Locator( self, f"{system_obj}_target_loc", system_obj, 0 )
    cmds.setAttr( f'{target_obj}.inheritsTransform', 0 ) #Make target unaffected by the camera's transforms so it behaves like directly under the world
    cmds.setAttr( f'{target_obj}.overrideEnabled', 1 )
    # Color
    cmds.setAttr( f'{target_obj}.overrideRGBColors', 1 )
    cmds.setAttr( f'{target_obj}.overrideColorRGB', self.ui_data[f'target_color'][0], self.ui_data[f'target_color'][1], self.ui_data[f'target_color'][2] )
    cmds.setAttr( f'{target_obj}.useOutlinerColor', 1 )
    cmds.setAttr( f'{target_obj}.outlinerColor', self.ui_data['target_color'][0], self.ui_data['target_color'][1], self.ui_data['target_color'][2] )
    # Selectable
    if self.ui_data[f'target_select'] == "Non selectable":
        cmds.setAttr( f'{target_obj}.overrideDisplayType', 2 )
    # Display
    if not self.ui_data['target_display']:
        cmds.setAttr( f'{target_obj}.visibility', 0 )
    
    #Aim
    aim_obj = cmds.createNode( 'transform', name=f"{system_obj}_aim", parent=system_obj, skipSelect=True )
    _Lock_Transf( aim_obj )
    aim_zero_obj = cmds.createNode( 'transform', name=f"{system_obj}_aim_zero", parent=aim_obj, skipSelect=True )
    cmds.setAttr( f'{aim_obj}.inheritsTransform', 0 ) #Make aim unaffected by the camera's transforms to skip space pre matrix
    cmds.setAttr( f'{aim_zero_obj}.translateX', float(self.ui_data['aim_dist']) )
    cmds.setAttr( f'{aim_obj}.visibility', 0 )
    cmds.setAttr( f'{aim_zero_obj}.visibility', 0 )
    aimmtx = cmds.createNode( 'aimMatrix', name=f"{system_obj}_aimmtx", skipSelect=True )
    cmds.setAttr( f'{aimmtx}.primaryInputAxis', 1, 0, 0 )
    cmds.setAttr( f'{aimmtx}.secondaryInputAxis', 0, 1, 0 )
    cmds.setAttr( f'{aimmtx}.secondaryMode', 1 )
    cmds.setAttr( f'{aimmtx}.secondaryTargetVector', 0, 1, 0 )
    cmds.connectAttr( f'{system_obj}.worldMatrix[0]', f'{aimmtx}.inputMatrix' )
    cmds.connectAttr( f'{target_obj}.worldMatrix[0]', f'{aimmtx}.primaryTargetMatrix' )
    cmds.connectAttr( f'{system_obj}.worldMatrix[0]', f'{aimmtx}.secondaryTargetMatrix' )
    cmds.connectAttr( f'{aimmtx}.outputMatrix', f'{aim_obj}.offsetParentMatrix' )
    cmds.setAttr( f'{aimmtx}.enable', 0 )

    #World scale compensation system so crosses and trails aren't affected by scaled camera's transform
    sys_scfmtx = cmds.createNode( 'scaleFromMatrix', name=f"{system_obj}_scfmtx", skipSelect=True )
    sys_cmpmtx = cmds.createNode( 'composeMatrix', name=f"{system_obj}_cmpmtx", skipSelect=True )
    cmds.connectAttr( f'{system_obj}.worldInverseMatrix[0]', f'{sys_scfmtx}.input' )
    cmds.connectAttr( f'{sys_scfmtx}.output', f'{sys_cmpmtx}.inputScale' )

    #Cross
    cross_grp = cmds.createNode( 'transform', name=f"{system_obj}_cross_grp", parent=system_obj, skipSelect=True )
    _Lock_Transf( cross_grp )
    cross_obj = _Create_Locator( self, f"{system_obj}_cross_ref", cross_grp, 1 )
    cmds.connectAttr( f'{sys_cmpmtx}.outputMatrix', f'{cross_grp}.offsetParentMatrix' )
    cmds.setAttr( f'{cross_grp}.overrideEnabled', 1 )
    # Color
    cmds.setAttr( f'{cross_grp}.overrideRGBColors', 1 )
    cmds.setAttr( f'{cross_grp}.overrideColorRGB', self.ui_data[f'cross_color'][0], self.ui_data[f'cross_color'][1], self.ui_data[f'cross_color'][2] )
    # Selectable
    if self.ui_data[f'cross_select'] == "Non selectable":
        cmds.setAttr( f'{cross_grp}.overrideDisplayType', 2 )
    # Display
    if not self.ui_data['cross_display']:
        cmds.setAttr( f'{cross_grp}.visibility', 0 )

    #Trail
    trail_grp = cmds.createNode( 'transform', name=f"{system_obj}_trail_grp", parent=system_obj, skipSelect=True )
    _Lock_Transf( trail_grp )
    trail_obj = _Create_Locator( self, f"{system_obj}_trail_ref", trail_grp, 2 )
    cmds.connectAttr( f'{sys_cmpmtx}.outputMatrix', f'{trail_grp}.offsetParentMatrix' )
    cmds.setAttr( f'{trail_grp}.overrideEnabled', 1 )
    # Color
    cmds.setAttr( f'{trail_grp}.overrideRGBColors', 1 )
    cmds.setAttr( f'{trail_grp}.overrideColorRGB', self.ui_data[f'trail_color'][0], self.ui_data[f'trail_color'][1], self.ui_data[f'trail_color'][2] )
    # Selectable
    if self.ui_data[f'trail_select'] == "Non selectable":
        cmds.setAttr( f'{trail_grp}.overrideDisplayType', 2 )
    # Display
    if not self.ui_data['trail_display']:
        cmds.setAttr( f'{trail_grp}.visibility', 0 )
    
    #Store object names into ui_data
    self.ui_data['target_obj'] = target_obj
    self.ui_data['aim_zero_obj'] = aim_zero_obj
    self.ui_data['aimmtx'] = aimmtx
    self.ui_data['cross_grp'] = cross_grp
    self.ui_data['cross_obj'] = cross_obj
    self.ui_data['trail_grp'] = trail_grp
    self.ui_data['trail_obj'] = trail_obj

    #Switch from button build system to button calculate
    _Switch_MainBttn( self, 0 )
    cmds.inViewMessage( message="<font color=lime>System successfully built!</font color>", position="botCenter", fade=True, fadeOutTime=300 )
    print( "[INFO]: System succesfully built!" )

def Calculate( self, self_idx:int, partial_empty=None ): #Calculate motion trail
    """
    Calculate motion trail\n
    ### Parameters:\n
    'self' (None/Local_MotionTrail_Window): class object. If None, autofilled with the help of 'self_idx'\n
    'self_idx' (int): class object index in global_win_instances\n
    'partial_empty' (bool): (To ignore) Extra 'False' argument from partial() when function call includes argument(s)
    """
    if self is None:
        self = _Get_Instance( self_idx )
    
    #region - Check variables
    if self.ui_data['system'] is None:
        cmds.error( f"[ISSUE]: No system, please set an existing system or create one", noContext=True )
    if not cmds.objExists( self.ui_data['system'] ):
        cmds.error( f"[ISSUE]: No object '{self.ui_data['system']}' found!", noContext=True )
    
    if self.ui_data['camera'] is None:
        cmds.error( f"[ISSUE]: No camera set, please set a camera", noContext=True )
    if not cmds.objExists( self.ui_data['camera'] ):
        cmds.error( f"[ISSUE]: No object '{self.ui_data['camera']}' found!", noContext=True )

    if self.ui_data['aim_zero_obj'] is None or not cmds.objExists( self.ui_data['aim_zero_obj'] ):
        cmds.error( f"[ISSUE]: System's aim_zero object '{self.ui_data['aim_zero_obj']}' can't be found, you may have to delete and rebuild the system", noContext=True )
    if self.ui_data['target_obj'] is None or not cmds.objExists( self.ui_data['target_obj'] ):
        cmds.error( f"[ISSUE]: System's reference target object '{self.ui_data['target_obj']}' can't be found, you may have to delete and rebuild the system", noContext=True )
    
    if self.ui_data['cross_grp'] is None or not cmds.objExists( self.ui_data['cross_grp'] ):
        cmds.error( f"[ISSUE]: System's cross_grp object '{self.ui_data['cross_grp']}' can't be found, you may have to delete and rebuild the system", noContext=True )
    if self.ui_data['cross_obj'] is None or not cmds.objExists( self.ui_data['cross_obj'] ):
        cmds.error( f"[ISSUE]: System's reference cross object '{self.ui_data['cross_obj']}' can't be found, you maye have to delete and rebuild the system", noContext=True )
    if self.ui_data['trail_grp'] is None or not cmds.objExists( self.ui_data['trail_grp'] ):
        cmds.error( f"[ISSUE]: System's trail_grp object '{self.ui_data['trail_grp']}' can't be found, you may have to delete and rebuild the system", noContext=True )
    if self.ui_data['trail_obj'] is None or not cmds.objExists( self.ui_data['trail_obj'] ):
        cmds.error( f"[ISSUE]: System's reference trail object '{self.ui_data['trail_obj']}' can't be found, you maye have to delete and rebuild the system", noContext=True )
    
    if self.ui_data['step'] == 0:
        cmds.error( f"[ISSUE]: Step at 0 would loop infinitely, calculate stopped", noContext=True )
    #endregion - Check variables

    #Pre-calculate context
    prectx_frame = cmds.currentTime( query=True )
    prectx_autokey = True if cmds.autoKeyframe( query=True, state=True ) else False
    if prectx_autokey:
        cmds.autoKeyframe( state=False, noReset=True )
    
    #Make sure temporary calculation nodes don't already exist
    calc_nodes = ( f"{self.ui_data['system']}_disdim", f"{self.ui_data['system']}_trail_aim_ref" )
    for c_node in calc_nodes:
        if cmds.objExists( c_node ):
            cmds.delete( c_node )

    #Range data
    step = self.ui_data['step']
    step_positive = True if step >= 0 else False
    calcul_range = None
    frame_as_int = False
    # Raw range
    if self.ui_data['range'] == "Slider":
        calcul_range = ( cmds.playbackOptions( query=True, minTime=True ), cmds.playbackOptions( query=True, maxTime=True ) )
    elif self.ui_data['range'] == 'anim':
        calcul_range = ( cmds.playbackOptions( query=True, animationStartTime=True ), cmds.playbackOptions( query=True, animationEndTime=True ) )
    else:
        calcul_range = ( self.ui_data['cstm_range'][0], self.ui_data['cstm_range'][1] )
    # Convert float range to integer or Decimal float range and include last frame in the range
    if calcul_range[0] % 1 == 0 and calcul_range[1] % 1 == 0 and self.ui_data['step'] % 1 == 0:
        #To integers
        step = int(step)
        calcul_range = ( int(calcul_range[0]), int(calcul_range[1])+step ) #Convert to integer and increase end of range to include it
        frame_as_int = True
    else:
        #To Decimal floats
        step = deci.Decimal(f'{step}')
        calcul_range = ( deci.Decimal(f'{calcul_range[0]}'), deci.Decimal(f'{calcul_range[1]}')+step )
    # Check range isn't infinite
    if not step_positive and calcul_range[0] < calcul_range[1]:
        #Revert pre-calculate context
        if prectx_autokey:
            cmds.autoKeyframe( state=True, noReset=True )
        cmds.currentTime( prectx_frame )
        cmds.error( f"[ISSUE]: Step is negative but end-of-range is higher than start-of-range, this would continue infinitely", noContext=True )
    #Scale fix
    do_scale_fix = True if self.ui_data['scale_fix'] and self.ui_data['pool'] == 0 else False
    sys_scfmtx_out = None
    if do_scale_fix:
        sys_scfmtx_out = cmds.connectionInfo( f"{self.ui_data['system']}.worldInverseMatrix[0]", destinationFromSource=True )[0]
        sys_scfmtx_out = f"{sys_scfmtx_out.rsplit('.',1)[0]}.output"
    
    #Calculate data
    do_cancel=False
    c_frame = calcul_range[0] if frame_as_int else float(calcul_range[0]) #If not using integers, convert c_frame to float as cmds.currentTime doesn't support Decimal float
    pre_frame = c_frame - 1 if step_positive else c_frame + 1
    cross_name = f"{self.ui_data['cross_obj'].rsplit('_',1)[0]}"
    trail_name = f"{self.ui_data['trail_obj'].rsplit('_',1)[0]}"
    not_first_frame = False
    aim_pos = f"{self.ui_data['aim_zero_obj']}.worldMatrix[0]"
    c_pos = None
    last_pos = None
    c_cross_pos = None
    last_cross_pos = None
    last_cross = None
    last_cross_shape = None
    no_cross_idx = None if self.ui_data['cross_calcul'] else 0
    tangent_in = "stepnext"
    tangent_out = "step"
    cross_attr = ( 'translate', 'scale', 'visibility' ) if do_scale_fix else ( 'translate', 'visibility' )
    trail_attr = ( 'translate', 'rotate', 'scaleZ', 'visibility' )
    do_pool = False if self.ui_data['pool'] == 0 else True
    pool_idx = 0 if do_pool else None
    pool_suffixes = []
    pool_complete = False
    cross_no_calcul_pool = None

    #Enable aim matrix
    cmds.setAttr( f"{self.ui_data['aimmtx']}.enable", 1 )
    #Create utility nodes
    dis_dim = None
    trail_aimmtx = None
    trail_aim_ref = None
    if self.ui_data['trail_calcul']:
        dis_dim = cmds.createNode( 'transform', name=f"{self.ui_data['system']}_disdim", skipSelect=True )
        cmds.setAttr( f'{dis_dim}.visibility', 0 )
        dis_dim = cmds.createNode( 'distanceDimShape', name=f"{self.ui_data['system']}_disdimShape", parent=dis_dim, skipSelect=True )
        trail_aimmtx = cmds.createNode( 'aimMatrix', name=f"{self.ui_data['system']}_trail_aimmtx", skipSelect=True )
        cmds.setAttr( f'{trail_aimmtx}.primaryInputAxis', 0, 0, 1 )
        cmds.setAttr( f'{trail_aimmtx}.primaryMode', 1 )
        cmds.setAttr( f'{trail_aimmtx}.secondaryInputAxis', 0, 1, 0 )
        cmds.setAttr( f'{trail_aimmtx}.secondaryMode', 2 )
        cmds.connectAttr( f"{self.ui_data['aim_zero_obj']}.worldMatrix[0]", f'{trail_aimmtx}.inputMatrix' )
        cmds.connectAttr( f"{self.ui_data['aim_zero_obj']}.worldMatrix[0]", f'{trail_aimmtx}.secondaryTargetMatrix' )
        trail_aim_ref = cmds.createNode( 'transform', name=f"{self.ui_data['system']}_trail_aim_ref", skipSelect=True )
        cmds.connectAttr( f'{trail_aimmtx}.outputMatrix', f'{trail_aim_ref}.offsetParentMatrix' )
    #Rebuild feature
    if self.ui_data['rebuild']:
        #Clear duplicates
        _Clear_Elements( self_idx )
    else:
        #Hide duplicates
        element_grps = ( 'cross_grp', 'trail_grp' )
        for element in element_grps:
            children = cmds.listRelatives( self.ui_data[element], children=True )
            for child in children:
                cmds.setAttr( f'{child}.visibility', 0 )
                if do_pool:
                    cmds.setKeyframe( child, time=pre_frame, respectKeyable=True, inTangentType=tangent_in, outTangentType=tangent_out )
    #Prepare first-index trail pool item
    if do_pool and self.ui_data['trail_calcul']:
        c_trail = f"{trail_name}{f'{c_frame}'.replace('-','n',1).replace('.','_',1)}"
        if not cmds.objExists( c_trail ):
            c_trail = cmds.duplicate( self.ui_data['trail_obj'], name=c_trail )
        cmds.setKeyframe( c_trail, time=pre_frame, attribute='visibility', value=0, respectKeyable=True, inTangentType=tangent_in, outTangentType=tangent_out )
    #Prepare non-calcul crosses if needed
    if not self.ui_data['cross_calcul']:
        cross_start = cmds.duplicate( self.ui_data['cross_obj'], name=f"{cross_name}s" )[0]
        cross_end = cmds.duplicate( self.ui_data['cross_obj'], name=f"{cross_name}e" )[0]
        cross_no_calcul_pool = ( cross_start, cross_end )
        cmds.setAttr( f'{cross_start}.visibility', 1 )
        cmds.setAttr( f'{cross_end}.visibility', 1 )
    
    #Progress window
    progress_step = None
    progress_range = None
    if step % 1 == 0: #Step integer
        progress_step = int(step) if step_positive else int(step) * -1
        progress_range = int(calcul_range[1] - calcul_range[0])
        if progress_range < 0: #If range negative, turn positive
            progress_range *= -1
    else: #Step float
        t_step = step if step_positive else step * -1 #Make sure to have t_step positive
        progress_range = int((calcul_range[1] - calcul_range[0]) * t_step) if t_step > 1 else int((calcul_range[1] - calcul_range[0]) / t_step)
        if progress_range < 0: #If range negative, turn positive
            progress_range *= -1
        progress_step = 1
    cmds.progressWindow( endProgress=True )
    cmds.progressWindow( title="Local MotionTrail", status="Calculating...    <font color=darkorange>(Hold Esc to cancel)</font color>", isInterruptable=True, minValue=0, maxValue=progress_range, progress=0 )

    #Calculate
    while (step_positive and c_frame < calcul_range[1]) or (not step_positive and c_frame > calcul_range[1]):
        cmds.currentTime( c_frame, update=True )
        #Current position
        c_pos = cmds.getAttr( aim_pos )
        c_pos = ( c_pos[12], c_pos[13], c_pos[14] )
        if c_pos != last_pos: #If no superposition
            c_frame_suffix = f'{c_frame}'.replace('-','n',1).replace('.','_',1) if not do_pool or not pool_complete else pool_suffixes[pool_idx]
            
            #Cross
            if self.ui_data['cross_calcul']:
                if do_pool: #Pool
                    if self.ui_data['rebuild'] and not pool_complete: #-1 Pool not complete, duplicate new element
                        c_cross = cmds.duplicate( self.ui_data['cross_obj'], name=f"{cross_name}{c_frame_suffix}" )[0]
                        cmds.setKeyframe( c_cross, time=pre_frame, attribute=cross_attr, inTangentType=tangent_in, outTangentType=tangent_out )
                    else: #-1 Recycle pool
                        c_cross = f"{cross_name}{c_frame_suffix}"
                else: #Not pool
                    if self.ui_data['rebuild']: #-2 Rebuild all
                        c_cross = cmds.duplicate( self.ui_data['cross_obj'], name=f"{cross_name}{c_frame_suffix}" )[0]
                    else: #-2 Recycle
                        c_cross = f"{cross_name}{c_frame_suffix}"
                        if not cmds.objExists( c_cross ): #-3 Out of already built
                            c_cross = cmds.duplicate( self.ui_data['cross_obj'], name=f"{cross_name}{c_frame_suffix}" )[0]
                cmds.setAttr( f'{c_cross}.visibility', 1 )
            else: #No calcul cross
                c_cross = cross_no_calcul_pool[no_cross_idx]
                no_cross_idx = 0 if no_cross_idx else 1
            cmds.matchTransform( c_cross, self.ui_data['aim_zero_obj'], position=True, rotation=False, scale=False )
            c_cross_pos = cmds.getAttr( f'{c_cross}.translate' )[0]
            if do_scale_fix: #Scale fix on c_cross
                l_scale = cmds.getAttr( sys_scfmtx_out )[0]
                l_scale = ( 1.0 / l_scale[0], 1.0 / l_scale[1], 1.0 / l_scale[2] )
                cmds.setAttr( f'{c_cross}.scale', l_scale[0], l_scale[1], l_scale[2] )
        
            #Trail
            if not_first_frame and self.ui_data['trail_calcul']:
                if do_pool: #Pool
                    if self.ui_data['rebuild'] and not pool_complete: #-1 Pool not complete, duplicate new element
                        c_trail = cmds.duplicate( self.ui_data['trail_obj'], name=f"{trail_name}{c_frame_suffix}" )[0]
                        cmds.setKeyframe( c_trail, time=pre_frame, attribute=trail_attr, inTangentType=tangent_in, outTangentType=tangent_out )
                    else: #-1 Recycle pool
                        c_trail = f"{trail_name}{c_frame_suffix}"
                else: #No pool
                    if self.ui_data['rebuild']: #-1 Rebuild all
                        c_trail = cmds.duplicate( self.ui_data['trail_obj'], name=f"{trail_name}{c_frame_suffix}" )[0]
                    else: #-2 Recycle
                        c_trail = f"{trail_name}{c_frame_suffix}"
                        if not cmds.objExists( c_trail ): #-3 Out of already built
                            c_trail = cmds.duplicate( self.ui_data['trail_obj'], name=f"{trail_name}{c_frame_suffix}" )[0]
                cmds.setAttr( f'{c_trail}.visibility', 1 )
                #Position
                target_value = ( (last_cross_pos[0] + c_cross_pos[0]) *0.5, (last_cross_pos[1] + c_cross_pos[1]) *0.5, (last_cross_pos[2] + c_cross_pos[2]) *0.5 )
                cmds.setAttr( f'{c_trail}.translate', target_value[0], target_value[1], target_value[2] )

                #Rotation
                cmds.connectAttr( f'{last_cross}.worldMatrix[0]', f'{trail_aimmtx}.primaryTargetMatrix', force=True )
                cmds.matchTransform( c_trail, trail_aim_ref, position=False, rotation=True, scale=False )

                #Scale
                c_cross_shape = cmds.listRelatives( c_cross, children=True, shapes=True )[0]
                cmds.connectAttr( f'{last_cross_shape}.worldPosition[0]', f'{dis_dim}.startPoint', force=True )
                cmds.connectAttr( f'{c_cross_shape}.worldPosition[0]', f'{dis_dim}.endPoint', force=True )
                target_value = cmds.getAttr( f'{dis_dim}.distance' ) * 0.5
                cmds.setAttr( f'{c_trail}.scaleZ', target_value )
                last_cross_shape = c_cross_shape
            if do_pool: #Keyframe new values on current pool element(s)
                if self.ui_data['cross_calcul']:
                    cmds.setKeyframe( c_cross, attribute=cross_attr, inTangentType=tangent_in, outTangentType=tangent_out )
                if self.ui_data['trail_calcul'] and not_first_frame:
                    cmds.setKeyframe( c_trail, attribute=trail_attr, inTangentType=tangent_in, outTangentType=tangent_out )
            last_pos = c_pos
            last_cross_pos = c_cross_pos
            last_cross = c_cross
        
        #To next loop
        if frame_as_int:
            c_frame+=step
        else:
            c_frame = float( deci.Decimal(f'{c_frame}') + step )
        if do_pool:
            if not pool_complete:
                pool_suffixes.append( c_frame_suffix )
            if pool_idx < self.ui_data['pool']:
                pool_idx+=1
            else:
                pool_idx = 0
                pool_complete = True
        if not not_first_frame:
            not_first_frame = True
            last_cross_shape = cmds.listRelatives( c_cross, children=True, shapes=True )[0]
        cmds.progressWindow( edit=True, step=progress_step )
        if cmds.progressWindow( query=True, isCancelled=True ): #Check cancel call
            do_cancel=True
            break


    #Disable aim matrix
    cmds.setAttr( f"{self.ui_data['aimmtx']}.enable", 0 )
    #Clear utility nodes
    if self.ui_data['trail_calcul']:
        dis_dim = cmds.listRelatives( dis_dim, parent=True, fullPath=True )[0]
        cmds.delete( dis_dim )
        if trail_aimmtx is not None:
            cmds.delete( trail_aimmtx )
            cmds.delete( trail_aim_ref )
    
    #If non-calcul crosses, remove them
    if not self.ui_data['cross_calcul']:
        cmds.delete( cross_no_calcul_pool )
    
    #Progress window
    cmds.progressWindow( endProgress=True )
    
    #Revert pre-calculate context
    if prectx_autokey:
        cmds.autoKeyframe( state=True, noReset=True )
    cmds.currentTime( prectx_frame )
    if do_cancel:
        cmds.inViewMessage( message="<font color=darkorange>Motion trail calcul cancelled!</font color>", position="botCenter", fade=True, fadeOutTime=300 )
        print( "[INFO]: Motion trail calcul cancelled!" )
    else:
        cmds.inViewMessage( message="<font color=lime>Motion trail calcul done!</font color>", position="botCenter", fade=True, fadeOutTime=300 )
        print( f"[INFO]: Motion trail calcul done for '{self.ui_data['system']}'!" )

def Calculate_All( idx_range=None ): #Call Calculate() for multiple instances
    """
    Call Calculate() for multiple instances\n
    ### Parameters:\n
    'idx_range' (None/int/list/tuple): Instance index(es) to calculate\n
      -None: Calculate all instances\n
      -Int: Calculate specific instance index\n
      -List/Tuple: If one value, start from this index on the instances list [value0 :]\n
                Else start by index first value and end at index second value included [value0 : value1[
    """
    
    instances = None
    if idx_range is None:
        instances = (global_win_instances)
    else:
        if type(idx_range) == int:
            #Specific index
            if idx_range > global_win_count:
                cmds.error( f"[ISSUE]: 'idx_range' out of range! ( Max range is {global_win_count} )", noContext=True )
            instances = (global_win_instances[idx_range],)
        elif type(idx_range) == list or type(idx_range) == tuple:
            if len(idx_range) == 1:
                #Custom start
                instances = global_win_instances[idx_range[0]:]
            else:
                #Custom start and end
                instances = global_win_instances[idx_range[0]:idx_range[1]+1]

    if instances is not None:
        i = 0
        for c_instance in instances:
            if c_instance is not None and c_instance.ui_data['system'] is not None:
                Calculate( c_instance, i )
            i+=1

def Clear_Element( self, self_idx:int, element_idx:int, skip_warning=False, partial_empty=None ): #Clear duplicates of an element
    """
    Clear duplicates of an element\n
    ### Parameters:\n
    'self' (None/Local_MotionTrail_Window): class object. If None, autofilled with the help of 'self_idx'\n
    'self_idx' (int): class object index in global_win_instances\n
    'element_idx' (int): Element index ( 1:cross, 2:trail )\n
    'skip_warning' (bool): Used by calculate, skip already cleared element warning\n
    'partial_empty' (bool): (To ignore) Extra 'False' argument from partial() when function call includes argument(s)
    """
    if self is None:
        self = _Get_Instance( self_idx )
    
    #Check if system exists
    if self.ui_data['system'] is None or not cmds.objExists( self.ui_data['system'] ):
        cmds.warning( f"[ISSUE]: System '{self.ui_data['system']}' doesn't seem to exist (yet?)", noContext=True )
        return
    
    element_grp = 'cross_grp' if element_idx == 1 else 'trail_grp'
    element_obj = 'cross_obj' if element_idx == 1 else 'trail_obj'
    #Check if element group and element reference exist
    if self.ui_data[element_grp] is None or not cmds.objExists( self.ui_data[element_grp] ):
        cmds.error( f"[ISSUE]: Can't find element group '{self.ui_data[element_grp]}'!", noContext=True )
    if self.ui_data[element_obj] is None or not cmds.objExists( self.ui_data[element_obj] ):
        cmds.error( f"[ISSUE]: Can't find reference element '{self.ui_data[element_obj]}'!", noContext=True )
    
    children = cmds.listRelatives( self.ui_data[element_grp], children=True )
    if children is None:
        cmds.warning( f"[ISSUE]: Nothing found under element group '{self.ui_data[element_grp]}'!", noContext=True )
    else:
        children.remove( self.ui_data[element_obj] )
        if children != []:
            cmds.delete( children )
        elif not skip_warning:
            cmds.warning( f"[INFO]: Element already cleared!", noContext=True )

def Delete_System( self, self_idx:int, partial_empty=None ): #Delete system
        """
        Delete system\n
        ### Parameters:\n
        'self' (None/Local_MotionTrail_Window): class object. If None, autofilled with the help of 'self_idx'\n
        'self_idx' (int): class object index in global_win_instances\n
        'partial_empty' (bool): (To ignore) Extra 'False' argument from partial() when function call includes argument(s)
        """
        if self is None:
            self = _Get_Instance( self_idx )
        
        if self.ui_data['system'] is None or not cmds.objExists( self.ui_data['system'] ):
            cmds.error( f"[ISSUE]: Can't find system '{self.ui_data['system']}'!", noContext=True )
        
        cmds.delete( self.ui_data['system'] )
        _Switch_MainBttn( self, 1 )

def Close( self_idx:int ): #Close a specific instance and it's window
    """
    Close a specific instance and it's window\n
    ### Parameters:\n
    'self_idx' (int): class object index in global_win_instances
    """
    global global_win_instances
    global global_win_count

    if global_win_instances[self_idx] is None:
        return
    if self_idx > len(global_win_instances):
        cmds.error( f"[ISSUE]: Instance index {self_idx} out of range!", noContext=True )
    _Pick_Cancel( None, self_idx )
    global_win_instances[self_idx] = None

    all_none = True
    for c_instance in global_win_instances:
        if c_instance is not None:
            all_none = False
            break
    if all_none:
        global_win_instances.clear()
        global_win_count = 0
    
def Close_All(): #Close all instances and their window
    """ Close all instances and their window """
    global global_win_instances
    global global_win_count
    
    for c_instance in global_win_instances:
        if c_instance is None:
            continue
        elif cmds.window( c_instance.WIN_NAME, query=True, exists=True ):
            cmds.deleteUI( c_instance.WIN_NAME, window=True )
    global_win_instances.clear()
    global_win_count = 0

def Print_Global(): #Print global window instances
    """ Print global window instances """
    print( global_win_count, global_win_instances )
    i = 0
    for c_instance in global_win_instances:
        print( i, c_instance )
        i+=1

def Print_Data( self_idx=None ): #Print data from each global window instances
    """
    Print data from each global window instances\n
    ### Parameters:\n
    'self_idx' (None/int): If None, print for every instances else the instance at called index
    """
    instances_list = None
    i = None
    #Get instance(s)
    if self_idx is None:
        instances_list = global_win_instances
        i = 0
    else:
        if self_idx != 0 and self_idx > global_win_count-1:
            cmds.error( f"[ISSUE]: Index {self_idx} out of range! (Range max: {global_win_count-1})", noContext=True )
        else:
            instances_list = (global_win_instances[self_idx],)
            i = self_idx
    #Print
    for c_instance in instances_list:
        if c_instance is None:
            print( f"Instance {i} data: None" )
        else:
            print( f"Instance {i} data:" )
            for c_data in c_instance.ui_data.items():
                print( f"  '{c_data[0]}': {c_data[1]}" )
        i+=1
#endregion - * Public *
#endregion --- Functions ---